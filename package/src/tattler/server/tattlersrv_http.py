import json
import re
import os
import logging
from typing import Optional
from urllib.parse import urlparse, parse_qsl
from datetime import datetime, date
from pathlib import Path
from importlib.resources import files

import http.server

from tattler.server import sendable
from tattler.server import pluginloader   # import in this exact way to ensure that namespaces are aligned with those in the plugin import!

from tattler.server.templatemgr import get_scopes
from tattler.server import tattler_utils

def getenv(varname: str, defaultval: Optional[str]=None) -> Optional[str]:
    """Wrapper for getenv() to simplify mocking during testing"""
    return os.getenv(varname, defaultval)


logging.basicConfig(level=getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)

default_master_mode = 'debug'

def replace_time_values(obj):
    """Transform any time value in an object into a serializable form"""
    if isinstance(obj, dict):
        return {k:replace_time_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_time_values(v) for v in obj]
    elif isinstance(obj, str):
        # date?
        for t in [date, datetime]:
            try:
                return t.fromisoformat(obj)
            except ValueError:
                pass
    return obj

notification_req_re = re.compile(r'/notification/(?P<scope>[a-zA-Z0-9:._-]+)/((?P<event>[a-zA-Z0-9:._-]+)(?P<evprop>/vectors/)?)?')

class TattlerServer(http.server.BaseHTTPRequestHandler):
    def send(self, code, body):
        """Send response back to client, with given status code and payload."""
        if not isinstance(body, bytes):
            body = body.encode()
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def get_definitions(self):
        """Collect user-defined variables to expand into template from user's request."""
        blen = int(self.headers.get('Content-Length', 0))
        if blen == 0:
            return dict()
        if self.headers.get_content_type() != 'application/json':
            log.warning("Client %s sent content with unknown type %s. Rejecting", self.client_address, self.headers.get_content_type())
            raise ValueError(f"Invalid content type {self.headers.get_content_type()}")
        log.debug("Reading definitions from body ...")
        try:
            raw_body = self.rfile.read(blen).decode()
            log.debug("Received payload '%s'", raw_body)
            definitions = json.loads(raw_body)
            definitions = replace_time_values(definitions)
        except Exception as exc:
            log.exception("Could not deserialize definitions:")
            raise ValueError("Invalid definitions in body. Want JSON dictionary.") from exc
        return definitions

    def do_GET(self) -> None:
        """Handler for GET requests"""
        log.info("%s", self.requestline)
        if self.path == '/notification/':
            # serve list of scopes
            scopes = sorted(get_scopes(get_templates_path()))
            log.info("Sending scopes: %s", scopes)
            return self.send(200, json.dumps(scopes))
        reqparts = notification_req_re.match(self.path)
        if reqparts is None:
            log.warning("Error with invalid request %s. Expected RE '%s'.", self.path, notification_req_re.pattern)
            return self.send_error(404, "Unknown path requested")
        scope = reqparts.group('scope')
        event = reqparts.group('event')
        # serve list of events in scope
        if event and not reqparts.group('evprop'):
            return self.send_error(404, "Unknown path requested")
        try:
            tman = tattler_utils.get_template_manager(get_templates_path(), scope)
        except ValueError:
            return self.send_error(400, f"Unknown scope '{scope}'")
        if event is None:
            events = sorted(tman.available_events())
            return self.send(200, json.dumps(events))
        if not reqparts.group('evprop'):
            self.send_error(404, f"Unknown path requested. Did you mean {self.path}/vectors/ ?")
        # serve list of vectors in event
        vectors = sorted(tman.available_vectors(event))
        return self.send(200, json.dumps(vectors))

    def do_POST(self):
        """Handler for POST requests"""
        log.info("%s", self.requestline)
        try:
            urlp = urlparse(self.path)
        except ValueError:
            log.error("Unable to parse request %s from %s", self.requestline, self.client_address)
            return self.send_error(400)
        # parse request params
        reqparts = notification_req_re.match(self.path)
        if reqparts is None:
            log.warning("Error with invalid request %s. Expected RE '%s'.", self.path, notification_req_re.pattern)
            return self.send_error(404, "Unknown path requested")
        qr_params = {x:y for x, y in parse_qsl(urlp.query, strict_parsing=True)} if urlp.query else dict()
        log.debug("Got qr params: %s", qr_params)
        correlation_id = qr_params.get('correlationId', tattler_utils.mk_correlation_id())
        scope = reqparts.group('scope')
        event = reqparts.group('event')
        try:
            recipient_user = qr_params['user']
        except KeyError:
            log.warning("Missing 'user' param in %s (corrId=%s)", self.client_address, correlation_id)
            return self.send_error(400, f"Required parameter 'user' is missing (corrId={correlation_id}).")
        try:
            vectors = qr_params.get('vector', None)
            if vectors is not None:
                vectors = {v.strip().lower() for v in vectors.split(',')}
                unknown_vectors = vectors - set(sendable.vector_sendables.keys())
                assert set() == unknown_vectors
        except AssertionError:
            log.info("Rejecting req as client provided unknown vector '%s'", unknown_vectors)
            return self.send_error(400, f"Invalid vectors provided '{unknown_vectors}'")
        mode = tattler_utils.get_operating_mode(qr_params.get('mode', None), default_master_mode)
        # get definitions
        try:
            definitions = self.get_definitions()
        except Exception as err:
            return self.send_error(400, f"Unable to get definitions: {err}")
        log.info("<-%s:Sending corrId=%s; ev=%s@%s; rcpt=%s; v=%s; defs=%s...", self.client_address, correlation_id, event, scope, recipient_user, vectors, definitions)
        # do send
        try:
            notif_jobs = tattler_utils.send_notification_user_vectors(get_templates_path(), recipient_user, vectors, scope, event, definitions, correlation_id, mode=mode)
            if not notif_jobs:
                return self.send_error(400, f"Unknown recipient {recipient_user} - no contacts found.")
        except ValueError as err:
            log.exception("Client request failed with %s", err)
            return self.send_error(400, f"Invalid value provided: {err}")
        except Exception as err:
            log.exception("Error sending notif %s: %s", correlation_id, err)
            return self.send_error(500, f"Unable to send: {err}")
        log.info("Notification sent. %s", notif_jobs)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(notif_jobs).encode("utf-8"))

def serve(address='', port=20000):
    """Start server instance listening on given TCP address and port"""
    log.warning("serving at %s:%s", address, port)
    try:
        return http.server.HTTPServer((address, port), TattlerServer)
    except OSError as err:
        log.error("Unable to bind %s: %s", (address, port), err)

def get_templates_path() -> Path:
    """Check validity and return path to templates from environment settings, or default.
    
    If envvar TATTLER_TEMPLATE_BASE is set, use that.
    Else, use the internal path to native demo templates.
    """
    templproc_base_path = getenv('TATTLER_TEMPLATE_BASE')
    if templproc_base_path:
        templproc_base_path = Path(templproc_base_path)
    else:
        templproc_base_path = files('tattler.templates').joinpath('.')
    try:
        tattler_utils.get_template_manager(templproc_base_path)
        return templproc_base_path
    except ValueError as err:
        log.error("Template directory ('%s') check failed. Fix this before notification requests come in. I do real-time loading, so I'll keep going now.", err)
    return templproc_base_path

def parse_opts_and_serve():
    """Collect server endpoint settings from environment and start server on them."""
    host, port = getenv('TATTLER_LISTEN_ADDRESS', '127.0.0.1:11503').rsplit(':', 1)
    tprocpath = get_templates_path()
    assert tprocpath is not None
    log.info("Using templates from %s", tprocpath)
    port = int(port)
    return serve(host, port)

def main():
    """Logic run when module run as main"""
    tattler_utils.init_plugins(getenv("TATTLER_PLUGIN_PATH"))
    try:
        srv = parse_opts_and_serve()
        if srv:
            srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
