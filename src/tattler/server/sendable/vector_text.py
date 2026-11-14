"""Generic sendable for plain-text vectors, delivered through DeliveryBackend plug-ins"""

import logging
import os
from typing import Iterable, Optional, Mapping, Any, Sequence, Tuple

from tattler.server.sendable import vector_sendable
from tattler.server.sendable import delivery_backend


logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)


class TextSendable(vector_sendable.Sendable):
    """A plain-text message for any vector delivered through :py:class:`DeliveryBackend` plug-ins.

    Bind the class to a vector by setting :py:attr:`vector_name` — either in a subclass, or
    dynamically as done by :py:func:`sendable.get_vector_class` for vectors that are only
    declared by delivery backend plug-ins.

    Recipient validation is delegated to the vector's backends: a recipient is valid iff at
    least one configured backend accepts it, and the first accepting backend normalizes it.
    """

    # name of the vector this class delivers for; bound by subclasses or by sendable.get_vector_class()
    vector_name: Optional[str] = None

    @classmethod
    def vector(cls) -> str:
        assert cls.vector_name, f"{cls.__name__} used without binding vector_name to a vector."
        return cls.vector_name

    @classmethod
    def validate_configuration(cls) -> None:
        """Raise iff a configuration parameter is missing or invalid, including the delivery backends'.

        :raise ValueError:     when any part of the configuration is invalid; exception message describes what."""
        super().validate_configuration()
        delivery_backend.get_backends(cls.vector())

    def validate_recipient(self, recipient: str) -> str:
        """Return the recipient normalized by the first backend of this vector that accepts it.

        :param recipient:   Recipient address to validate.

        :raise ValueError:  when no configured backend of this vector accepts the recipient.

        :return:            Normalized recipient address."""
        errors = []
        for backend in delivery_backend.get_backends(self.vector()):
            try:
                return backend.validate_recipient(recipient)
            except ValueError as err:
                errors.append(f"{backend.name()}: {err}")
        raise ValueError(f"No configured {self.vector()} backend accepts recipient '{recipient}'. {' '.join(errors)}")

    def do_send(self, recipients: Iterable[str], context: Optional[Mapping[str, Any]]=None, priority: Optional[int]=None):
        # generate message content first, to avoid loading rest if template has issues
        context = context or {}
        msg_content = self.content(context=context)
        backends = delivery_backend.get_backends(self.vector())
        log.debug("n%s: Body: %s", self.nid, msg_content)
        # split notifications by sender
        senderids = {}
        for r in recipients:
            senderids.setdefault(self.sender(r), set()).add(r)
        for senderid, rcpts in senderids.items():
            backend, result = self._send_with_failover(backends, rcpts, msg_content, senderid, priority)
            report = backend.delivery_status(result)
            if report:
                log.info("n%s: Delivery report: %s", self.nid, report)

    def _send_with_failover(self, backends: Sequence['delivery_backend.DeliveryBackend'], recipients: Iterable[str], body: str, sender: Optional[str], priority: Optional[int]) -> Tuple['delivery_backend.DeliveryBackend', 'delivery_backend.SendResult']:
        """Try each backend in order until one accepts the message; raise if all refuse.

        :raise ValueError:  when every configured backend failed to accept the message.

        :return:            The backend that accepted the message, and its send result."""
        last_err = None
        for backend in backends:
            log.info("n%s: Sending %s to '%s' via %s", self.nid, self.vector(), recipients, backend.name())
            try:
                return backend, backend.send(recipients, body, sender=sender, priority=priority)
            except Exception as err:
                log.warning("n%s: Backend %s failed to accept %s to '%s' (%s). Trying next backend, if any.", self.nid, backend.name(), self.vector(), recipients, err)
                last_err = err
        raise ValueError(f"All configured {self.vector()} backends failed to accept message to '{recipients}'.") from last_err
