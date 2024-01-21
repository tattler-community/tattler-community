import os
import logging
import uuid
from typing import Mapping, Any, Optional, Iterable
from pathlib import Path

from tattler.server import pluginloader           # import in this exact way to ensure that namespaces are aligned with those in the plugin import!

from tattler.server.templatemgr import TemplateMgr
from tattler.server import sendable
from tattler.server.sendable.template_processor import TemplateProcessor
from tattler.server.templateprocessor_jinja import JinjaTemplateProcessor


mode_severity = ['debug', 'staging', 'production']


template_processors_available = {
    'plain': TemplateProcessor,
    'jinja': JinjaTemplateProcessor,
}
# set via envvar
default_template_processor_name = 'jinja'
template_processor = None

# search for native plugins in the following paths
native_plugins_path = [Path(__file__).parent / 'plugins']

# trim long notification IDs at this number of characters
max_notification_id_len = 12

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)

ContextType = Mapping[str, Any]

def getenv(name: str, default: Optional[str]=None) -> Optional[str]:
    """Get variable from environment -- allowing mocking"""
    return os.getenv(name, default)

def init_plugins(search_path: Optional[str|os.PathLike]=None) -> None:
    """Load plugins, if any path for them is available.
    
    :param search_path:     Path to a directory holding plug-in files, or None to only load native plug-ins."""
    initpaths = []
    if search_path is not None:
        search_path = Path(search_path)
        if search_path.is_dir():
            initpaths = [search_path]
        else:
            log.warning("Ignoring plug-in path '%s' as it's not a directory. Fix with envvar TATTLER_PLUGIN_PATH.", search_path)
    initpaths += native_plugins_path
    pluginloader.init([str(x) for x in initpaths])


def guess_first_name(email_address: str) -> Optional[str]:
    """Return a user's first name, guessed from email address"""
    phony_usernames = ('info', 'mail', 'noc', 'webmaster', 'root', 'hostmaster', 'sysadmin', 'postmaster', 'dns', 'ns', 'abuse', 'admin', 'hello', 'hi', 'it')
    def _clean(n):
        c = n.strip().lower()
        # phony?
        if c in phony_usernames:
            return None
        # numbers only?
        if c.isnumeric():
            return None
        # remove heading and trailing numbers
        c = c.strip('0123456789')
        return c.capitalize()
    try:
        u, _ = email_address.split('@')
        assert u
    except Exception as err:
        raise ValueError(f"Malformed email address '{email_address}'") from err
    separators = '._-+'
    for sep in [s for s in separators if s in u]:
        name = u.split(sep, 1)[0]
        if len(name) >= 2:
            return _clean(name)
    return _clean(u)

def get_template_processor() -> TemplateProcessor:
    """Return a suitable template processor for the type of template configured."""
    return template_processors_available[getenv("TATTLER_TEMPLATE_TYPE", default_template_processor_name).lower()]

def get_template_manager(base_path: str | os.PathLike, scope_name: Optional[str]=None) -> TemplateMgr:
    """Return a suitable template manager for a given template path and scope name."""
    if isinstance(base_path, str):
        base_path = Path(base_path)
    if scope_name is not None:
        base_path = base_path.joinpath(scope_name) if scope_name else base_path
    return TemplateMgr(base_path)

def mk_correlation_id(prefix: Optional[str]='tattler') -> str:
    """Generate a random correlation ID, for sessions where none has been pre-provided."""
    if prefix:
        return f'{prefix}:{uuid.uuid4()}'
    return str(uuid.uuid4())

def core_template_variables(recipient_user: str, correlationId: Optional[str], mode: str, vector: str, event_scope: str, event_name: str) -> ContextType:
    """Return a set of variables to be fed to every template."""
    # contacts
    recipient_contacts = pluginloader.lookup_contacts(recipient_user)
    try:
        userfirstname = guess_first_name(recipient_contacts['email'])
    except Exception:
        log.info("Can't get first name for #%s (email: %s) -- using 'user'.", recipient_user, recipient_contacts.get('email', None))
        userfirstname = 'user'
    user_accounttype = recipient_contacts.get('account_type', 'unknown')
    corrId = correlationId or mk_correlation_id()
    notId = corrId.rsplit(':', 1)[1] if ':' in corrId else corrId
    notId = notId[-max_notification_id_len:]
    return {
        'user_email': recipient_contacts.get('email', None),
        'user_sms': recipient_contacts.get('sms', None),
        'user_firstname': userfirstname,
        'user_account_type': user_accounttype,
        'user_language': recipient_contacts.get('language', None),
        'correlation_id': corrId,
        'notification_id': notId,
        'notification_mode': mode,
        'notification_vector': vector,
        'notification_scope': event_scope,
        'event_name': event_name,
    }

def plugin_template_variables(context: ContextType) -> ContextType:
    """Solicit plugins to get variables to be fed into templates."""
    return pluginloader.process_context(context)

def send_notification_user_vectors(base_path, recipient_user, vectors, event_scope, event_name, context=None, correlationId=None, mode='debug') -> Iterable[str]:
    """Send a notification to a recipient across a set of vectors, and return the list of vectors which succeeded"""
    if context is None:
        context = {}
    try:
        tman = get_template_manager(base_path, event_scope)
    except ValueError as err:
        log.error("Scope does not exist: '%s' under '%s'. Error was: '%s'", event_scope, base_path, err)
        raise ValueError(f"Scope does not exist: '{event_scope}'") from err
    if event_name not in tman.available_events():
        log.error("Event does not exist: '%s' in scope '%s' (base = '%s'). Rejecting notification", event_name, event_scope, base_path)
        raise ValueError(f"Event does not exist: '{event_name}' in scope '{event_scope}'")
    if mode is None:
        mode = 'debug'
    if mode not in sendable.modes:
        raise ValueError(f"Invalid mode {mode}. Expected one of {sendable.modes}")
    retval = []
    event_vectors = set(tman.available_vectors(event_name))
    if vectors is None:
        vectors = event_vectors
    if not (set(vectors) & event_vectors):
        msg = "None of the requested vectors %s is available for event %s, which only supports %s. Returning error."
        params = (vectors, event_name, event_vectors)
        log.error(msg, *params)
        raise ValueError(msg % params)
    log.debug("<-Request to send #%s to %s (cid=%s)", recipient_user, vectors, correlationId)
    user_contacts = pluginloader.lookup_contacts(recipient_user)
    if user_contacts is None:
        log.warning("Recipient unknown '%s'. Aborting notification.", recipient_user)
        raise ValueError(f"Recipient unknown '{recipient_user}'. Aborting notification.")
    log.debug("Contacts for recipient %s are: %s", recipient_user, user_contacts)
    user_available_vectors = {vname for vname in vectors if user_contacts.get(vname, None) is not None}
    usrlang = None
    log.info("Recipient %s is reachable over %d vectors of the %d requested: %s", recipient_user, len(user_available_vectors), len(vectors), user_available_vectors)
    for vname in user_available_vectors:
        if usrlang is not None:
            log.debug("User #%s has language preference '%s' -> checking if it's supported by the event template ...")
            veclangs = tman.available_languages(event_name, vname)
            if usrlang not in veclangs:
                msg = f"User '{recipient_user}' has language '{usrlang}', which is not available for {event_name}:{vname}@{event_scope}. Available languages for it are: {veclangs}."
                raise ValueError(msg)
        recipient = user_contacts[vname]
        template_context = core_template_variables(recipient_user, correlationId, mode, vname, event_scope, event_name)
        if context:
            template_context.update(context)
        template_context = plugin_template_variables(template_context)
        errmsg = None
        log.info("Sending %s:%s (evname:language) to #%s@%s => [%s], context=%s (cid=%s)", event_name, usrlang, recipient_user, vname, recipient, template_context, correlationId)
        blacklist = getenv('TATTLER_BLACKLIST_PATH')
        try:
            sendable.send_notification(vname, event_name, [recipient], template_base=tman.base_path, context=template_context, mode=mode, template_processor=get_template_processor(), blacklist=blacklist, language_code=usrlang)
        except Exception as err:
            errmsg = str(err)
            log.exception("Error sending %s for %s:%s@%s (evname:lang@scope) to %s. Skipping vector. (cid=%s)", vname, event_name, usrlang, event_scope, recipient, correlationId)
            log.debug("Context was (cid=%s): %s", correlationId, template_context)
        retval.append({
            'id': f"{vname}:{uuid.uuid4()}",
            'vector': vname,
            'resultCode': 1 if errmsg else 0,
            'result': 'error' if errmsg else 'success',
            'detail': errmsg or 'OK'
        })
    return retval

def get_operating_mode(requested_mode, default_master_mode=None):
    """Return the operating mode based on requested and allowed (master) mode."""
    master_mode = getenv('TATTLER_MASTER_MODE') or default_master_mode
    master_mode.strip().lower()
    if master_mode not in mode_severity:
        raise RuntimeError(f"'TATTLER_MASTER_MODE' envvar is set to unsupported value '{master_mode}' not in {mode_severity}.")
    if not requested_mode:
        return master_mode
    if requested_mode not in mode_severity:
        raise RuntimeError(f"Requested mode is set to unsupported value '{requested_mode}' not in {mode_severity}.")
    if mode_severity.index(requested_mode) > mode_severity.index(master_mode):
        return master_mode
    return requested_mode
