"""Interface separating message assembly from concrete delivery through a provider.

Delivery backends are tattler plug-ins like any other: tattler ships its own (see
``sendable/backends/``), and users may supply additional ones through the regular
plug-in mechanism by subclassing :py:class:`DeliveryBackend` in a module within
``TATTLER_PLUGIN_PATH``. Both are loaded the same way, by :py:mod:`pluginloader`.

Backends declare which vector they deliver for with :py:meth:`DeliveryBackend.vector`;
deliveries group all configured backends by vector, and fail over within the group.
"""

import logging
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional, Sequence

from tattler.server import pluginloader
from tattler.server.sendable import vector_sendable

log = logging.getLogger(__name__)


@dataclass
class SendResult:
    """Provider-native identifiers returned by a send, usable to look up delivery status later.

    :param recipient_ids:   Map of recipient number to the provider's message identifier for it.
    :param batch_id:        Provider's identifier for the whole batch, if it issues one instead of per-recipient IDs.
    """
    recipient_ids: Mapping[str, str] = field(default_factory=dict)
    batch_id: Optional[str] = None


@dataclass
class DeliveryStatus:
    """Normalized delivery state of a message to one recipient.

    :param status:      One of 'pending', 'sent', 'delivered', 'failed', 'unknown'.
    :param raw_status:  Provider's native status string, for logging and debugging.
    :param cost:        Realized delivery cost in the provider's native unit, if reported.
    :param detail:      Free-form provider detail, e.g. failure reason.
    """
    status: str
    raw_status: Optional[str] = None
    cost: Optional[float] = None
    detail: Optional[str] = None


class DeliveryBackend(pluginloader.TattlerPlugin):
    """Base class for delivery providers of any vector.

    Backends declare the vector they deliver for in :py:meth:`vector` and their
    configuration in :py:attr:`required_settings` (keyed by envvar suffix), and
    implement :py:meth:`send`; :py:meth:`cost` and :py:meth:`delivery_status`
    are optional. A backend is only used when its configuration is present and valid.
    """

    plugin_category = 'deliverybackend'

    # map of envvar suffix to [required: bool, validator: Optional[callable]]; see envvar()
    required_settings = {}

    @classmethod
    def vector(cls) -> str:
        """Return the name of the vector this backend delivers for.

        :return:    Vector name, e.g. 'sms'."""
        raise NotImplementedError("DeliveryBackend subclasses must declare their vector().")   # pragma: no cover

    @classmethod
    def name(cls) -> str:
        """Return the identifier of this backend, used to namespace its settings.

        Defaults to the class name, lowercased and with any 'backend' suffix dropped.

        :return:    Lowercase backend name, e.g. 'bulksms'."""
        return cls.__name__.lower().removesuffix('backend')

    @classmethod
    def envvar(cls, suffix: str) -> str:
        """Return the name of the environment variable holding a given setting of this backend.

        :param suffix:  Setting name as declared in required_settings.

        :return:        Full environment variable name, e.g. 'TATTLER_BULKSMS_TOKEN'."""
        return f"TATTLER_{cls.name().upper()}_{suffix.upper()}"

    @classmethod
    def validate_configuration(cls) -> None:
        """Raise iff a configuration setting of this backend is missing or invalid.

        :raise PluginNotConfigured: When required settings are missing and none of the backend's settings is provided.
        :raise ValueError:          When any required setting is missing or any provided setting is malformed."""
        values = {suffix: vector_sendable.getenv(cls.envvar(suffix)) for suffix in cls.required_settings}
        unconfigured = all(val is None for val in values.values())
        for suffix, (mandatory, validator) in cls.required_settings.items():
            varname, val = cls.envvar(suffix), values[suffix]
            if val is None:
                if mandatory:
                    errtype = pluginloader.PluginNotConfigured if unconfigured else ValueError
                    raise errtype(f"Required setting '{varname}' to deliver {cls.vector()} via {cls.name()} is missing.")
            elif validator and not validator(val.strip()):
                raise ValueError(f"Setting '{varname}'='{val.strip()}' is malformed.")

    @classmethod
    def available(cls) -> bool:
        """Return whether this backend is usable, i.e. its configuration is present and valid.

        :return:    True iff validate_configuration() would not raise."""
        try:
            cls.validate_configuration()
        except ValueError:
            return False
        return True

    def setup(self) -> None:
        """Validate the backend's configuration upon loading, so problems surface at startup.

        :raise PluginNotConfigured: When the backend is not configured at all.
        :raise ValueError:          When the backend's configuration is incomplete or invalid."""
        self.validate_configuration()

    @classmethod
    def validate_recipient(cls, recipient: str) -> str:
        """Return the recipient normalized for this backend, or raise if the backend cannot deliver to it.

        Permissive default: accept any recipient unchanged. Override to declare the address
        format of the vector this backend delivers for.

        :param recipient:   Recipient address as requested, e.g. '+19876543210'.

        :raise ValueError:  When this backend cannot deliver to this recipient.

        :return:            Normalized recipient address."""
        return recipient

    def cost(self, recipients: Iterable[str], body: str, sender: Optional[str]=None) -> Optional[float]:
        """Estimate the delivery cost before sending, in the provider's native unit.

        Best-effort: providers without a pre-send quoting facility return None.

        :param recipients:  Recipient numbers the message would be sent to.
        :param body:        Text that would be sent.
        :param sender:      Sender ID that would be used, if any.

        :return:            Estimated cost, or None if the provider cannot quote before sending."""
        return None

    def send(self, recipients: Iterable[str], body: str, sender: Optional[str]=None, priority: Optional[int]=None) -> SendResult:
        """Deliver a message to some recipients.

        :param recipients:  Recipient addresses, e.g. '+19876543210'.
        :param body:        Text of the message.
        :param sender:      Sender ID to deliver as, or None for the provider's default.
        :param priority:    Delivery priority, provider-specific interpretation.

        :raise ValueError:  When the provider rejected the request or returned an unusable response.

        :return:            Identifiers to look up delivery status with, see :py:meth:`delivery_status`."""
        raise NotImplementedError("DeliveryBackend subclasses must implement send().")   # pragma: no cover

    def delivery_status(self, result: SendResult) -> Mapping[str, DeliveryStatus]:
        """Look up the delivery status of a previously-sent message.

        Best-effort: providers without a status-polling facility return an empty map.

        :param result:  Result of the send() call to look up status for.

        :return:        Map of recipient address to its delivery status; empty if the provider cannot report it."""
        return {}


def plugin_vectors() -> set[str]:
    """Return the vector names declared by the currently loaded delivery backend plug-ins.

    :return:    Names of the vectors deliverable through some configured backend."""
    return {plugin.vector() for plugin in pluginloader.loaded_plugins.get(DeliveryBackend.plugin_category, {}).values()}


def get_backends(vector: str) -> Sequence['DeliveryBackend']:
    """Return every backend of a vector whose configuration is complete and valid, in delivery order.

    Collects both backends shipped with tattler and user-supplied ones, both loaded by
    :py:mod:`pluginloader` the same way, keeping only those declaring the requested vector.

    :param vector:  Name of the vector to collect backends for, e.g. 'sms'.

    :raise ValueError:  When no backend is configured for this vector.

    :return:            Ready backend instances, in the order deliveries should try them."""
    active = {
        plugin.name(): plugin
        for plugin in pluginloader.loaded_plugins.get(DeliveryBackend.plugin_category, {}).values()
        if plugin.vector() == vector
    }
    if not active:
        problems = [
            f"{name}: {err}"
            for name, (cls, err) in sorted(pluginloader.loaded_plugin_errors.get(DeliveryBackend.plugin_category, {}).items())
            if issubclass(cls, DeliveryBackend) and cls.vector() == vector
        ]
        raise ValueError(f"No {vector} backend is configured. {' '.join(problems)}")
    if len(active) > 1:
        log.info("Multiple %s backends configured; deliveries will try them in order: %s", vector, sorted(active))
    return [active[name] for name in sorted(active)]


pluginloader.register_plugin_class(DeliveryBackend)
