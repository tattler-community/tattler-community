import logging
import os
from typing import Optional, Iterable, Mapping, Any

from .template_processor import TemplateProcessor
from .blacklist import Blacklist

from tattler.server.sendable.vector_sendable import Sendable
from tattler.server.sendable.vector_text import TextSendable
from tattler.server.sendable.vector_sms import SMSSendable
from tattler.server.sendable.vector_email import EmailSendable
from tattler.server.sendable import delivery_backend

# map vector names to their associated Sendable class; see also get_vector_class() for
# vectors that are only declared by delivery backend plug-ins
vector_sendables = {
        'sms':      SMSSendable,
        'email':    EmailSendable,
        }

modes = {'debug', 'staging', 'production'}

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger('sendable')

# base class composed into every vector class; replaceable via register_sendable_base()
_sendable_base: type[Sendable] = Sendable

# cache of classes built for vectors that are only declared by delivery backend plug-ins
_dynamic_sendables: dict[str, type[Sendable]] = {}

def _compose_with_base(sendable_class: type[Sendable]) -> type[Sendable]:
    """Return the class extended with the registered sendable base, unless it already inherits it."""
    if issubclass(sendable_class, _sendable_base):
        return sendable_class
    return type(sendable_class.__name__, (sendable_class, _sendable_base), {})

def register_sendable_base(base_class: type[Sendable]) -> None:
    """Register the base class that every vector class is composed with.

    Extension hook: e.g. tattler enterprise edition registers its multilingual Sendable here,
    so every vector -- built-in or plug-in-declared -- gains multilingual template lookup.

    :param base_class:  Sendable subclass to compose into every vector class."""
    global _sendable_base
    assert issubclass(base_class, Sendable), f"Sendable base must subclass Sendable, got '{base_class}'."
    _sendable_base = base_class
    for vname, vclass in vector_sendables.items():
        vector_sendables[vname] = _compose_with_base(vclass)
    _dynamic_sendables.clear()

def register_vector_sendable(sendable_class: type[Sendable]) -> None:
    """Register a dedicated Sendable class for the vector it declares in vector().

    Only needed for vectors requiring custom message assembly (e.g. MIME for email): vectors
    declared by delivery backend plug-ins are otherwise served dynamically by get_vector_class().

    :param sendable_class:  Sendable subclass to register for its own vector() name."""
    vector_sendables[sendable_class.vector().lower()] = _compose_with_base(sendable_class)

def available_vectors() -> set[str]:
    """Return the names of all vectors currently deliverable.

    :return:    Names of built-in vectors plus those declared by loaded delivery backend plug-ins."""
    return set(vector_sendables) | delivery_backend.plugin_vectors()

def get_vector_class(vector_name: str) -> type[Sendable]:
    """Return the class to use to build notifications for a given vector name.

    Vectors without a registered class are served with a TextSendable bound to the vector name,
    as long as some loaded delivery backend plug-in declares that vector.

    :param vector_name:     Name of the vector for which the class should be returned.

    :raise ValueError:      When neither a registered class nor a delivery backend declares the vector.

    :return:                Reference to the class (type) for constructing the respective vector.
    """
    vname = vector_name.lower()
    if vname in vector_sendables:
        return vector_sendables[vname]
    if vname not in _dynamic_sendables:
        if vname not in delivery_backend.plugin_vectors():
            raise ValueError(f"Can't generate Sendable for unknown vector '{vector_name}'. Valid values: {sorted(available_vectors())}.")
        _dynamic_sendables[vname] = _compose_with_base(type(f'{vname.capitalize()}Sendable', (TextSendable,), {'vector_name': vname}))
    return _dynamic_sendables[vname]

def make_notification(vector: str, event: str, recipient_list: Iterable[str], template_processor: Optional[type[TemplateProcessor]]=None, template_base: Optional[str]=None, language_code: Optional[str]=None) -> Sendable:
    """Return a Sendable for a given event.

    Return a sendable for the given type, event, recipient. If 'context'
    is not specified, the sendable is left unbound, and must be bound
    before sending.
    
    :param vector:                  Name of vector to make notification for. See @vector_sendables
    :param event:                   Name of event to send.
    :param recipient_list:          Recipient address (vector-specific) to create notification for (not necessarily deliver to!).
    :param template_processor:      Class to expand() template into sendable bytes.
    :param template_base:           Path of directory holding templates for events (one folder per event name).
    :param language_code:           Send the event notification in the language with this codename.

    :return:                        Sendable object for delivery.
    """
    vector_class = get_vector_class(vector)
    kwargs = dict()
    if template_processor is not None:
        kwargs['template_processor'] = template_processor
    if template_base:
        kwargs['template_base'] = template_base
    if language_code:
        kwargs['language_code'] = language_code
    return vector_class(event, recipient_list, **kwargs)

def send_notification(vector: str, event: str, recipient_list: Iterable[str], context: Optional[Mapping[str, Any]]=None, template_processor: Optional[type[TemplateProcessor]]=None, template_base: Optional[str]=None, priority: Optional[int]=None, mode: Optional[str]=None, blacklist: Optional[str]=None, language_code: Optional[str]=None) -> None:
    """Send a notification to a recipient list."""
    ntf = make_notification(vector, event, recipient_list, template_processor=template_processor, template_base=template_base, language_code=language_code)
    kwargs = {}
    if priority is not None:
        kwargs['priority'] = priority
    if mode is not None:
        kwargs['mode'] = mode
    if blacklist is not None:
        try:
            ntf.blacklist(blacklist)
        except OSError as e:
            log.warning("Error loading requested blacklist file '%s' -- I'll ignore it: %s", blacklist, e)
    ntf.send(context=context, **kwargs)
