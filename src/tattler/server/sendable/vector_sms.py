"""SMS sendable"""

import re
import logging
import os
from typing import Iterable, Optional, Mapping, Any

from tattler.server.sendable import vector_sendable
from tattler.server.sendable.vector_sendable import getenv

from .bulksms import BulkSMS


logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)

ENVVAR_NAME = 'TATTLER_BULKSMS_TOKEN'


def get_auth_from_environment():
    """Get authentication data configured."""
    authstr = getenv(ENVVAR_NAME, None)
    assert authstr, f"Presence of auth config '{ENVVAR_NAME}' must be pre-validated before get_auth_from_environment()"
    tid, tsecr = None, None
    try:
        tid, tsecr = authstr.strip().split(':', 1)
    except ValueError as err:
        log.warning("Envvar '%s' is malformed: required 'user:pass' or 'tokenid:secret'.", ENVVAR_NAME)
        raise ValueError(f"Envvar '{ENVVAR_NAME}' is malformed: required 'user:pass' or 'tokenid:secret'.") from err
    return tid, tsecr


class SMSSendable(vector_sendable.Sendable):
    """An SMS message."""

    required_settings = {
        'TATTLER_BULKSMS_TOKEN': [True, lambda v: re.match(r'.+:.+', v)],
        'TATTLER_SMS_SENDER': [False, lambda v: re.match(r'\+[0-9]+', v)],
    }

    @classmethod
    def sender(cls, recipient: Optional[str]=None) -> Optional[str]:
        """Return the configured sender ID for a given recipient.

        The sender id is looked up in envvar TATTLER_SMS_SENDER. It returns its
        value if one is provided. If TATTLER_SMS_SENDER contains multiple values
        separated by a ',' -- then the option sharing the longest prefix with the
        recipient is returned. If no matches are found, the first value is returned.

        This is not an exact algorithm, but it fits realistic use cases.
        
        :param recipient:   Recipient for which the sender should be found; or None for default sender.
        
        :return:            ID to send the message as for the given recipient, or None if no configuration available."""
        confsender = super().sender(recipient)
        if not confsender:
            return None
        senders = confsender.strip().split(',')
        if not recipient or len(senders) == 1:
            return senders[0]
        # got multiple sender numbers. Find matching country code
        matching_prefixes = []
        for snd in senders:
            matching_prefixes += [snd[:i] for i in range(2, max(len(snd), len(recipient))) if snd[:i] == recipient[:i]]
        if matching_prefixes:
            mpref = max(matching_prefixes, key=len)
            return [x for x in senders if x.startswith(mpref)][0]
        return senders[0]

    def get_sms_server(self):
        """Prepare SMS server object."""
        credentials = get_auth_from_environment()
        return BulkSMS(*credentials)

    def validate_recipient(self, recipient: str) -> str:
        if re.match(r'(00|\+)[1-9][0-9]+', recipient):
            if recipient.startswith('00'):
                recipient = '+' + recipient[2:]
            return recipient
        raise ValueError(f"Recipient must be in International Calling format '+19876543210' or '001987654321', not '{recipient}'.")

    @classmethod
    def vector(cls: type[vector_sendable.Sendable]) -> str:
        return 'sms'

    def do_send(self, recipients: Iterable[str], priority: Optional[int]=None, context: Optional[Mapping[str, Any]]=None):
        # generate message content first, to avoid loading rest if template has issues
        context = context or {}
        msg_content = self.content(context=context)
        smssrv = self.get_sms_server()
        log.info("n%s: Sending SMS to '%s'", self.nid, recipients)
        log.debug("n%s: Body: %s", self.nid, msg_content)
        # split notifications by sender
        sms_senderids = {}
        for r in recipients:
            sms_senderids[self.sender(r)] = sms_senderids.get(self.sender(r), set()) | {r}
        for senderid, rcpts in sms_senderids.items():
            taskids = smssrv.send(rcpts, msg_content, sender=senderid, priority=priority)
        report = smssrv.msg_delivery_status(taskids[0])
        log.info("n%s: Delivery report: %s", self.nid, report)
