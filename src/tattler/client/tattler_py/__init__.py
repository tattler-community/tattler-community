"""Python client to access tattler server"""

import os
import logging
from typing import Mapping, Iterable, Tuple, Optional

# from tattler_py.tattler_client_grpc import tattlerClientGRPC
from tattler.client.tattler_py.tattler_client_http import TattlerClientHTTP, TattlerClient

from tattler.client.tattler_py.tattler_client_utils import mk_correlation_id, get_endpoint_config

log = logging.getLogger(__name__)
log.setLevel(os.getenv('LOG_LEVEL', 'info').upper())

def send_notification(scope: str, event: str, recipient: str, context: Optional[Mapping[str, str]]=None, correlationId: Optional[str]=None, mode: str='debug', vectors: Optional[Iterable[str]]=None, priority: Optional[bool]=None, srv_addr: Optional[str]=None, srv_port: Optional[int]=None) -> Tuple[bool, Optional[Mapping[str, str]]]:
    """All-in-one utility to connect to tattler server and send a notification.

    If both srv_addr and srv_port are None, they are looked up in envvar 'TATTLER_SRV_ADDR',
    which takes format 'address:port' (e.g. '192.168.1.1:11503' or 'fe80::12:11503'), before
    defaulting to '127.0.0.1' and 11503 respectively if that's not given.
    If you don't want configuration to be looked up in the environment, set either argument
    srv_addr or srv_port.
    
    :param scope:           The scope name to search the event in.
    :param event:           The event name to deliver.
    :param context:         Optional custom variables (name:value) to use for template expansion.
    :param correlationId:   correlation ID for tattler log when processing this request. Self-generated if missing.
    :param mode:            Notification mode in 'debug', 'staging', 'production'.
    :param vectors:         Restrict delivery to these vectors; 'None' delivers to all vectors declared by the event template.
    :param priority:        Embed this user-visible priority in the notification, where the vector supports it.
    :param srv_addr:        Contact tattler_server at this IP address. Default: 127.0.0.1
    :param srv_port:        Contact tattler_server at this port number. Default: 11503

    :return:                Whether delivery succeeded for at least one vector, and delivery details for all.
    """
    if srv_addr is None and srv_port is None:
        srv_addr, srv_port = get_endpoint_config('TATTLER_SERVER_ADDRESS')
    nsrv = TattlerClientHTTP(scope, srv_addr, srv_port, mode)
    context = context or {}
    corrid = correlationId or mk_correlation_id()
    log.info("Booking delivery %s@%s to #%s (m=%s,v=%s,p=%s,s=%s:%s,cid=%s)", event, scope, recipient, mode, vectors, priority, srv_addr, srv_port, correlationId)
    try:
        res = nsrv.send(vectors=vectors, event=event, recipient=recipient, context=context, priority=priority, correlationId=corrid)
    except Exception as err:
        return False, { 'error': str(err) }
    return True, res
