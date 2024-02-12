import logging
import os
from typing import Optional, Iterable, Mapping, Any

from .template_processor import TemplateProcessor
from .blacklist import Blacklist

from tattler.server.sendable.vector_sendable import Sendable
from tattler.server.sendable.vector_sms import SMSSendable
from tattler.server.sendable.vector_email import EmailSendable

# map vector names to their associated Sendable class
vector_sendables = {
        'sms':      SMSSendable,
        'email':    EmailSendable,
        }

modes = {'debug', 'staging', 'production'}

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger('sendable')

def get_vector_class(vector_name: str) -> type[Sendable]:
    """Return the class to use to build notifications for a given vector name.
    
    :param vector_name:     Name of the vector for which the class should be returned.
    
    :return:                Reference to the class (type) for constructing the respective vector.
    """
    try:
        return vector_sendables[vector_name.lower()]
    except KeyError as err:
        raise ValueError(f"Can't generate Sendable for unknown vector '{vector_name}'. Valid values: {list(vector_sendables)}.") from err

def make_notification(vector: str, event: str, recipient_list: Iterable[str], template_processor: type[TemplateProcessor]=TemplateProcessor, template_base: Optional[str]=None, language_code: Optional[str]=None) -> Sendable:
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
    if template_processor:
        kwargs['template_processor'] = template_processor
    if template_base:
        kwargs['template_base'] = template_base
    if language_code:
        kwargs['language_code'] = language_code
    return vector_class(event, recipient_list, **kwargs)

def send_notification(vector: str, event: str, recipient_list: Iterable[str], context: Optional[Mapping[str, Any]]=None, template_processor: type[TemplateProcessor]=TemplateProcessor, template_base: Optional[str]=None, priority: Optional[int]=None, mode: Optional[str]=None, blacklist: Optional[str]=None, language_code: Optional[str]=None) -> None:
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
