"""SMS sendable"""

import re
import logging
import os
from typing import Iterable, Optional, Mapping, Any

from .bulksms import BulkSMS

from .vector_sendable import Sendable, getenv

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)

ENVVAR_NAME = 'TATTLER_BULKSMS_TOKEN'


def get_auth_from_environment():
    """Get authentication data configured."""
    authstr = getenv(ENVVAR_NAME, None)
    if authstr is None:
        log.info("Envvar '%s' missing. Disabling SMS delivery as a vector.", ENVVAR_NAME)
        return None, None
    tid, tsecr = None, None
    try:
        tid, tsecr = authstr.strip().split(':', 1)
    except ValueError as err:
        log.warning("Envvar '%s' is malformatted: required 'user:pass' or 'tokenid:secret'.", ENVVAR_NAME)
        raise ValueError(f"Envvar '{ENVVAR_NAME}' is malformatted: required 'user:pass' or 'tokenid:secret'.") from err
    return tid, tsecr


class SMSSendable(Sendable):
    """An SMS message."""
    def get_sms_server(self):
        """Prepare SMS server object."""
        credentials = get_auth_from_environment()
        return BulkSMS(*credentials)

    def validate_recipient(self, recipient: str) -> str:
        if re.match(r'(00|\+)[1-9][0-9]+', recipient):
            # remove leading 00 and + for BulkSMS format
            if recipient.startswith('00'):
                recipient = '+' + recipient[2:]
            return recipient
        raise ValueError(f"Recipient must be in International Calling format '+19876543210' or '001987654321', not '{recipient}'.")

    @classmethod
    def vector(cls: type(Sendable)) -> str:
        return 'sms'

    def do_send(self, recipients: Iterable[str], priority: Optional[int]=None, context: Optional[Mapping[str, Any]]=None):
        # generate message content first, to avoid loading rest if template has issues
        context = context or {}
        msg_content = self.content(context=context)
        smssrv = self.get_sms_server()
        log.info("n%s: Sending SMS to '%s'", self.nid, recipients)
        log.debug("n%s: Body: %s", self.nid, self.content(context=context))
        sms_senderid = getenv('TATTLER_SMS_SENDERID', None)
        taskids = smssrv.send(recipients, msg_content, sender=sms_senderid, priority=priority)
        report = smssrv.msg_delivery_status(taskids[0])
        log.info("n%s: Delivery report: %s", self.nid, report)

