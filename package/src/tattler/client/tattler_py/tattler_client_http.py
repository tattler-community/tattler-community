"""Implementation of tattler client using HTTP interface to connect to tattler server"""

from urllib import request
from typing import Mapping, Iterable

from tattler.client.tattler_py.tattler_client import TattlerClient, log

from tattler.client.tattler_py.serialization import serialize_json, deserialize_json

class TattlerClientHTTP(TattlerClient):
    """HTTP implementation of TattlerClient"""

    def do_send(self, vectors: Iterable[str], event: str, recipient: str, context: Mapping[str, str]=None, priority: bool=False, correlationId: str=None) -> bool:
        url = f'http://{self.endpoint}/notification/{self.scope_name}/{event}/?user={recipient}'
        if vectors:
            url += f'&vector={",".join(vectors)}'
        if correlationId:
            url += f'&correlationId={correlationId}'
        if priority:
            url += f'&priority={priority}'
        if self.mode:
            url += f'&mode={self.mode}'
        headers = {}
        data = None
        if context:
            headers['Content-Type'] = 'application/json'
            data = serialize_json(context)
        req = request.Request(url, data=data, headers=headers, method='POST')
        try:
            log.debug("Sending request URL = '%s'", req.get_full_url())
            with request.urlopen(req) as f:
                res = f.read()
        except Exception as err:
            log.exception("Error {%s} sending notif %s: %s", type(err), correlationId, err)
            return False
        if not res:
            log.warning("Notification delivery to failed -- no data provided.")
            return False
        try:
            res = deserialize_json(res)
        except ValueError:
            log.exception("Unable to JSON-decode server response:")
            return False
        failed = [r for r in res if r.get('resultCode', 0) != 0]
        succeeded = [r for r in res if r.get('resultCode', None) == 0]
        if not succeeded:
            log.warning("Notification delivery to one or more vectors failed: %s", failed)
            return False
        log.info("Notif #%s successfully sent: %s", correlationId, res)
        return True

    def scopes(self):
        """Return list of vectors available events within this scope."""
        url = f'http://{self.endpoint}/notification/'
        with request.urlopen(url) as f:
            res = f.read()
            return deserialize_json(res)

    def events(self):
        """Return list of vectors available events within this scope."""
        url = f'http://{self.endpoint}/notification/{self.scope_name}/'
        with request.urlopen(url) as f:
            res = f.read()
            return deserialize_json(res)

    def vectors(self, event):
        """Return list of vectors available vectors within this scope."""
        url = f'http://{self.endpoint}/notification/{self.scope_name}/{event}/vectors/'
        with request.urlopen(url) as f:
            res = f.read()
            return deserialize_json(res)
