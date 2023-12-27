import logging
import os

from .template_processor import TemplateProcessor
from .blacklist import Blacklist

from .vector_sendable import Sendable
from .vector_email import EmailSendable
from .vector_sms import SMSSendable

# map vector names to their associated Sendable class
vector_sendables = {
        'sms':      SMSSendable,
        'email':    EmailSendable
        }

modes = {'debug', 'staging', 'production'}

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger('sendable')

def make_notification(vector, event, recipient_list, template_processor=TemplateProcessor, template_base=None) -> Sendable:
    """Return a Sendable for a given event.

    Return a sendable for the given type, event, recipient. If 'context'
    is not specified, the sendable is left unbound, and must be bound
    before sending.
    
    @param vector             [str]               Name of vector to make notification for. See @vector_sendables
    @param event              [str]               Name of event to send.
    @param recipient_list     [list of str]       Recipient address (vector-specific) to create notification for (not necessarily deliver to!).
    @param template_processor [TemplateProcessor] Class to expand() template into sendable bytes.
    @param template_base      [str]               Path of directory holding templates for events (one folder per event name).

    @return [Sendable]         Sendable object for delivery.
    """

    vector_class = vector_sendables.get(vector.lower(), None)
    if vector_class is None:
        raise ValueError("Can't generate Sendable for unknown vector '%s'. Valid values: %s." % (vector, str(list(vector_sendables.keys()))))
    kwargs = dict()
    if template_processor:
        kwargs['template_processor'] = template_processor
    if template_base:
        kwargs['template_base'] = template_base
    return vector_class(event, recipient_list, **kwargs)

def send_notification(vector, event, recipient_list, context=None, template_processor=TemplateProcessor, template_base=None, priority=None, mode=None, blacklist=None):
    """Send a notification to a recipient list."""
    ntf = make_notification(vector, event, recipient_list, template_processor=template_processor, template_base=template_base)
    kwargs = {}
    if priority is not None:
        kwargs['priority'] = priority
    if mode is not None:
        kwargs['mode'] = mode
    if blacklist is not None:
        try:
            ntf.blacklist(blacklist)
        except OSError as e:
            log.warning(f"Error loading requested blacklist file '{blacklist}' -- I'll ignore it: {e}")
    ntf.send(context=context, **kwargs)
