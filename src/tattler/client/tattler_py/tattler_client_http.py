"""Implementation of tattler client using HTTP interface to connect to tattler server"""

import json
from urllib import request, parse
from typing import Mapping, Iterable, Optional

from tattler.client.tattler_py.tattler_client import TattlerClient, log

from tattler.utils.serialization import serialize_json

class TattlerClientHTTP(TattlerClient):
    """HTTP implementation of TattlerClient"""

    def do_send(self, vectors: Iterable[str], event: str, recipient: str, context: Optional[Mapping[str, str]]=None, priority: bool=False, correlationId: Optional[str]=None) -> bool:
        """Perform the actual server request to send the notification"""
        url_path = f'http://{self.endpoint}/notification/{parse.quote(self.scope_name)}/{parse.quote(event)}/'
        params = {
            'user': recipient,
        }
        if vectors:
            params['vector'] = ",".join(sorted(vectors))
        if correlationId:
            params['correlationId'] = correlationId
        if priority:
            params['priority'] = priority
        if self.mode:
            params['mode'] = self.mode
        headers = {}
        data = None
        if context:
            headers['Content-Type'] = 'application/json'
            data = serialize_json(context)
        url = url_path + '?' + parse.urlencode(params)
        req = request.Request(url, data=data, headers=headers, method='POST')
        try:
            log.debug("Sending request URL = '%s'", req.get_full_url())
            with request.urlopen(req) as f:
                res: bytes = f.read()
        except Exception as err:
            log.error("Error communicating with tattler server %s: {%s} sending notif %s: %s", url, type(err), correlationId, err)
            raise
        if not res:
            log.warning("Notification delivery to failed -- no data provided.")
            raise ValueError(f"Error communicating with tattler server {url}: empty response.")
        try:
            rdec = res.decode()
            res = json.loads(rdec)
        except ValueError as err:
            log.error("Unable to JSON-decode server response: %s. Response was %d bytes, first 100B of which=%s...", err, len(rdec), rdec[:100])
            raise ValueError(f"Error communicating with tattler server: unparsable response: {err}. Response was {len(rdec)} bytes, first 100B of which={rdec[:100]}...") from err
        failed = [r for r in res if r.get('resultCode', 0) != 0]
        succeeded = [r for r in res if r.get('resultCode', None) == 0]
        if not succeeded:
            log.warning("Notification delivery to one or more vectors failed: %s", failed)
            raise ValueError(f"All requested delivery targets failed: {failed}")
        log.info("Notif #%s successfully sent: %s", correlationId, res)

    def scopes(self):
        """Return list of vectors available events within this scope."""
        url = f'http://{self.endpoint}/notification/'
        with request.urlopen(url) as f:
            return json.loads(f.read().decode())

    def events(self):
        """Return list of vectors available events within this scope."""
        url = f'http://{self.endpoint}/notification/{self.scope_name}/'
        with request.urlopen(url) as f:
            return json.loads(f.read().decode())

    def vectors(self, event):
        """Return list of vectors available vectors within this scope."""
        url = f'http://{self.endpoint}/notification/{self.scope_name}/{event}/vectors/'
        with request.urlopen(url) as f:
            return json.loads(f.read().decode())
