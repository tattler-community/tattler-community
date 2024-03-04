"""Client class for tattler"""

import re
import os
import logging
from datetime import datetime
import uuid
from abc import ABC
from typing import Mapping, Iterable, Optional
from tattler.client.tattler_py.serialization import serialize_json

from tattler.client.tattler_py.tattler_client_utils import getenv

log = logging.getLogger(__name__)
log.setLevel(getenv('LOG_LEVEL', 'info').upper())

_default_deadletter_path = os.path.join(os.sep, 'tmp', 'tattler_deadletter')

valid_modes = {'debug', 'staging', 'production'}

class TattlerClient(ABC):
    """Connection controller class to access tattler server functionality."""

    def __init__(self, scope_name: str, srv_addr: str='127.0.0.1', srv_port: int=11503, mode: str='debug') -> None:
        """Construct TattlerClient.
        
        :param scope_name:      Name of the scope to use when sending requests to server.
        :param srv_addr:        IP address to connect to for tattler_server.
        :param srv_port:        Port number to connect to for tattler_server.
        :param mode:            Operating mode to request when sending requests to server."""
        if not (srv_addr and srv_port):
            raise ValueError(f"Endpoint of server must be set. Values {srv_addr}:{srv_port}")
        self.endpoint = f'{srv_addr}:{srv_port}'
        if not re.match(r'^[a-zA-Z0-9-_.]+$', scope_name):
            raise ValueError(f"Invalid scope name '{scope_name}'. It only accepts alphanumeric sybols and '.', '_' or '-'.")
        self.scope_name = scope_name
        mode = mode.strip().lower()
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Valid values are: {valid_modes}")
        self.mode = mode

    def scopes(self) -> Optional[Iterable[str]]:
        """Return list of scopes available at this server."""
        return None

    def events(self) -> Optional[Iterable[str]]:
        """Return list of available events within this scope.

        :return:        List of events available within my scope, or None if unknown."""
        raise NotImplementedError("Not implemented")

    def vectors(self, event: str) -> Optional[Iterable[str]]:
        """Return list of vectors available vectors within this scope.
        
        :param event:   Name of event to check available vectors for.
        
        :return:        List of vectors available for the event within my scope, or None if unknown."""
        raise NotImplementedError("Not implemented")

    def send(self, vectors: Optional[Iterable[str]], event: str, recipient: str, context: Optional[Mapping[str, str]]=None, priority: bool=False, correlationId: str=None) -> bool:
        """Send a notification to a recipient list.
        
        :param vectors:         List of vector names to deliver the notification to, or None for 'all available'.
        :param event:           Name of the event to notify.
        :param recipient:       ID of the recipient to notify.
        :param context:         Dictionary of variable names and values to pass to server for template rendering, or None if empty.
        :param priority:        Whether the server should mark the notification as high-priority (e.g. in email); This may be controlled in the notification template itself too.
        :param correlationId:   Arbitrary string to identify this transaction with; the server will log this to allow tracing requests across different systems.

        :return:                Whether the request could be sent successfully to the server.
        """
        correlationId = correlationId or f"tattler_client_py:{uuid.uuid4()}"
        log.info("Sending e=%s to r=%s over v=%s with c=%s", event, recipient, vectors, context)
        try:
            return self.do_send(vectors, event, recipient, context=context, priority=priority, correlationId=correlationId)
        except Exception as err:
            log.exception("Delivery failed ('%s') corrId=%s", err, correlationId)
            self.deadletter_store({'vectors':vectors, 'event':event, 'recipient':recipient, 'context':context, 'priority':priority, 'correlationId':correlationId})
            return False

    def do_send(self, vectors: Optional[Iterable[str]], event: str, recipient: str, context: Optional[Mapping[str, str]]=None, priority: bool=False, correlationId: str=None) -> bool:
        """Implement this to concretely deliver over the custom channel.
        
        See :meth:`tattler.client.tattler_py.tattler_client.TattlerClient.send` .
        """
        raise NotImplementedError("Not implemented")

    def deadletter_store(self, params: Optional[Mapping[str, str]]=None) -> None:
        """Store an error into a deadletter file, if envvar TATTLER_DEADLETTER_PATH is configured.
        
        :param params:      Optional parameters to store (JSON-formmated) as part of the dead letter.
        """
        dldir_path = getenv("TATTLER_DEADLETTER_PATH", _default_deadletter_path)
        try:
            os.makedirs(dldir_path, exist_ok=True)
        except OSError as err:
            log.exception("Error creating deadletter path '%s' (giving up): %s", dldir_path, err)
            return

        dlname = f"{self.scope_name}_{params['recipient']}_{params['event']}_{os.getpid()}_{datetime.now().strftime('%s')}.txt"
        dlpath = os.path.join(dldir_path, dlname)
        params = params or {}
        try:
            with open(dlpath, 'w+', encoding='utf-8') as f:
                serdata = serialize_json(params)
                f.write(serdata.decode('utf-8'))
        except OSError as err:
            log.error("Error creating deadletter file %s upon failed notification. Giving up: %s", dlpath, err)
