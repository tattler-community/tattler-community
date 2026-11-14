"""SMS delivery backend for BulkSMS.com."""

import logging
import os
import re
from typing import Iterable, Mapping, Optional, Tuple

from bulksms import BulkSMS

from tattler.server.sendable import vector_sendable
from tattler.server.sendable.delivery_backend import DeliveryBackend, SendResult, DeliveryStatus

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)

# map BulkSMS's native delivery states onto the normalized DeliveryStatus vocabulary
_status_map = {
    'ACCEPTED': 'pending',
    'SCHEDULED': 'pending',
    'SENT': 'sent',
    'DELIVERED': 'delivered',
    'FAILED': 'failed',
}


class BulkSMSBackend(DeliveryBackend):
    """Deliver SMS through BulkSMS.com's JSON API, and poll it for delivery status."""

    @classmethod
    def vector(cls) -> str:
        return 'sms'

    required_settings = {
        'TOKEN': [True, lambda v: re.match(r'.+:.+', v)],
    }

    def get_auth(self) -> Tuple[str, str]:
        """Return the token pair configured for authentication.

        :raise ValueError:  When the configured value is not a ':'-separated pair.

        :return:            Token ID and token secret."""
        varname = self.envvar('TOKEN')
        authstr = vector_sendable.getenv(varname)
        assert authstr, f"Presence of auth config '{varname}' must be pre-validated before get_auth()"
        try:
            tid, tsecr = authstr.strip().split(':', 1)
        except ValueError as err:
            raise ValueError(f"Envvar '{varname}' is malformed: required 'user:pass' or 'tokenid:secret'.") from err
        return tid, tsecr

    def get_server(self) -> BulkSMS:
        """Return an authenticated session with the provider."""
        tid, tsecr = self.get_auth()
        return BulkSMS(token_id=tid, token_secret=tsecr)

    def send(self, recipients: Iterable[str], body: str, sender: Optional[str]=None, priority: Optional[int]=None) -> SendResult:
        recipients = list(recipients)
        srv = self.get_server()
        msgids = srv.send(recipients, body, sender=sender, priority=priority)
        return SendResult(recipient_ids=dict(zip(recipients, msgids)))

    def delivery_status(self, result: SendResult) -> Mapping[str, DeliveryStatus]:
        srv = self.get_server()
        statuses = {}
        for rcpt, msgid in result.recipient_ids.items():
            try:
                raw = srv.msg_status(msgid)
                rawstatus = raw['status']['type'].upper()
            except Exception as err:
                log.warning("Failed to look up delivery status of message '%s' to '%s': %s", msgid, rcpt, err)
                statuses[rcpt] = DeliveryStatus(status='unknown', detail=str(err))
                continue
            cost = raw.get('creditCost')
            statuses[rcpt] = DeliveryStatus(status=_status_map.get(rawstatus, 'unknown'), raw_status=rawstatus,
                                            cost=float(cost) if cost is not None else None)
        return statuses
