"""SMS sendable"""

import re
import logging
import os
from typing import Optional

# vector_sendable and delivery_backend are also the patch targets used by tests
from tattler.server.sendable import vector_sendable
from tattler.server.sendable import delivery_backend
from tattler.server.sendable.vector_text import TextSendable


logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)


class SMSSendable(TextSendable):
    """An SMS message."""

    vector_name = 'sms'

    required_settings = {
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

    def validate_recipient(self, recipient: str) -> str:
        if re.match(r'(00|\+)[1-9][0-9]+', recipient):
            if recipient.startswith('00'):
                recipient = '+' + recipient[2:]
            return recipient
        raise ValueError(f"Recipient must be in International Calling format '+19876543210' or '001987654321', not '{recipient}'.")
