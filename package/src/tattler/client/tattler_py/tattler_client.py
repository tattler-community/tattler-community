"""Client class for tattler"""

import os
import logging
from datetime import datetime
import uuid
from typing import Mapping, Iterable
from tattler.client.tattler_py.serialization import serialize_json

from tattler.client.tattler_py.tattler_client_utils import get_server_endpoint

log = logging.getLogger(__name__)
log.setLevel(os.getenv('LOG_LEVEL', 'info').upper())

_default_deadletter_path = os.path.join(os.sep, 'tmp', 'tattler_deadletter')

class TattlerClient:
    """Connection controller class to access tattler server functionality."""

    def __init__(self, scope_name: str, srv_addr: str=None, srv_port: int=11503, mode: str='debug') -> None:
        if not (srv_addr and srv_port):
            srv_addr, srv_port = get_server_endpoint()
        self.endpoint = f'{srv_addr}:{srv_port}'
        self.scope_name = scope_name
        self.mode = mode

    def scopes(self) -> Iterable[str] | None:
        """Return list of scopes available at this server."""
        return None

    def events(self) -> Iterable[str] | None:
        """Return list of available events within this scope."""
        return None

    def vectors(self, event: str) -> Iterable[str] | None:
        """Return list of vectors available vectors within this scope."""
        return None

    def send(self, vectors: Iterable[str], event: str, recipient: str, context: Mapping[str, str]=None, priority: bool=False, correlationId: str=None) -> bool:
        """Send a notification to a recipient list."""
        correlationId = correlationId or f"tattler_client_py:{uuid.uuid4()}"
        log.info("Sending e=%s to r=%s over v=%s with c=%s", event, recipient, vectors, context)
        try:
            return self.do_send(vectors, event, recipient, context=context, priority=priority, correlationId=correlationId)
        except Exception as err:
            log.exception("Delivery failed ('%s') corrId=%s", err, correlationId)
            self.deadletter_store({'vectors':vectors, 'event':event, 'recipient':recipient, 'context':context, 'priority':priority, 'correlationId':correlationId})
            return False

    def do_send(self, vectors: Iterable[str], event: str, recipient: str, context: Mapping[str, str]=None, priority: bool=False, correlationId: str=None) -> bool:
        """Implement this to concretely deliver over the custom channel"""
        return False

    def deadletter_store(self, params: Mapping[str, str]) -> None:
        """Store an error into a deadletter file, if envvar TATTLER_DEADLETTER_PATH is configured."""
        dldir_path = os.getenv("TATTLER_DEADLETTER_PATH", _default_deadletter_path)
        try:
            os.makedirs(dldir_path, exist_ok=True)
        except OSError as err:
            log.exception("Error creating deadletter path '%s' (giving up): %s", dldir_path, err)
            return

        dlname = f"{self.scope_name}_{params['recipient']}_{params['event']}_{os.getpid()}_{datetime.now().strftime('%s')}.txt"
        dlpath = os.path.join(dldir_path, dlname)
        try:
            with open(dlpath, 'w+', encoding='utf-8') as f:
                serdata = serialize_json(params)
                f.write(serdata.decode('utf-8'))
        except OSError as err:
            log.error("Error creating deadletter file %s upon failed notification. Giving up: %s", dlpath, err)
