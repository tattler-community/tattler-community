"""SMS sendable"""

import re
import logging
import os
from typing import Literal, Optional

# vector_sendable and delivery_backend are also the patch targets used by tests
from tattler.server.sendable import vector_sendable
from tattler.server.sendable import delivery_backend
from tattler.server.sendable.vector_text import TextSendable


logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)

SenderKind = Literal['number', 'name']


def sender_kind(sender: str) -> Optional[SenderKind]:
    """Classify an SMS sender ID, so that every backend treats it the same way.

    :param sender:  One sender ID, e.g. '+16315551234', '0016315551234' or 'Acme'.

    :return:        'number' for a mobile number in international calling format; 'name' for an alphanumeric name
                    of up to 11 characters including a letter; None if the sender is neither, hence invalid."""
    if re.fullmatch(r'(00|\+)[1-9][0-9]+', sender):
        return 'number'
    if re.fullmatch(r'[A-Za-z0-9]{1,11}', sender) and re.search(r'[A-Za-z]', sender):
        return 'name'
    return None


class SMSSendable(TextSendable):
    """An SMS message."""

    vector_name = 'sms'

    required_settings = {
        'TATTLER_SMS_SENDER': [False, lambda v: all(sender_kind(s) for s in v.split(','))],
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
