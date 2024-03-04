"""Python client to access tattler server"""

import os
import logging
from typing import Mapping, Iterable, Tuple, Optional

# from tattler_py.tattler_client_grpc import tattlerClientGRPC
from tattler.client.tattler_py.tattler_client_http import TattlerClientHTTP

from tattler.client.tattler_py.tattler_client_utils import mk_correlation_id

log = logging.getLogger(__name__)
log.setLevel(os.getenv('LOG_LEVEL', 'info').upper())

def send_notification(scope: str, event: str, recipient: str, context: Optional[Mapping[str, str]]=None, correlationId: Optional[str]=None, mode: str='debug', vectors: Optional[Iterable[str]]=None, priority: Optional[bool]=None, srv_addr: Optional[str]='127.0.0.1', srv_port: Optional[int]=11503) -> Tuple[bool, Optional[Mapping[str, str]]]:
    """All-in-one utility to connect to tattler server and send a notification.
    
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
    nsrv = TattlerClientHTTP(scope, srv_addr, srv_port, mode)
    context = context or {}
    corrid = correlationId or mk_correlation_id()
    log.info("Booking delivery %s@%s to #%s (m=%s,v=%s,p=%s,s=%s:%s,cid=%s)", event, scope, recipient, mode, vectors, priority, srv_addr, srv_port, correlationId)
    try:
        res = nsrv.send(vectors=vectors, event=event, recipient=recipient, context=context, priority=priority, correlationId=corrid)
    except Exception as err:
        return False, { 'error': str(err) }
    return True, res
