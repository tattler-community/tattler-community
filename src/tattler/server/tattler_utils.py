import base64
import os
import logging
import uuid
import binascii
from datetime import date, datetime
from typing import Mapping, Any, Optional, Iterable, Union
from pathlib import Path
from importlib.resources import files

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
    return os.getenv(name, default)     # pragma: no cover

def setenv(name: str, value: Optional[str]=None) -> None:
    """Set variable into environment -- allowing mocking"""
    os.environ[name] = value        # pragma: no cover

def init_plugins(search_path: Optional[Union[str, os.PathLike]]=None) -> None:
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

def mk_correlation_id(prefix: Optional[str]='tattler') -> str:
    """Generate a random correlation ID, for sessions where none has been pre-provided.
    
    :param prefix:      Optional string to prepend to the returned random ID ('prefix:id'); set to None for no string ('prefix').

    :return:            Random ID suitable for correlation logging, potentially prefixed with given prefix."""
    if prefix:
        return f'{prefix}:{uuid.uuid4()}'
    return str(uuid.uuid4())

def core_template_variables(recipient_user: str, correlationId: Optional[str], mode: str, vector: str, event_scope: str, event_name: str) -> ContextType:
    """Return a set of variables to be fed to every template."""
    # contacts
    recipient_contacts = pluginloader.lookup_contacts(recipient_user)
    userfirstname = None
    try:
        userfirstname = guess_first_name(recipient_contacts['email'])
    except Exception:
        log.info("Can't get first name for #%s (email: %s) -- using 'user'.", recipient_user, recipient_contacts.get('email', None))
    user_accounttype = recipient_contacts.get('account_type', 'unknown')
    corrId = correlationId or mk_correlation_id()
    notId = corrId.rsplit(':', 1)[1] if ':' in corrId else corrId
    notId = notId[-max_notification_id_len:]
    return {
        'user_id': recipient_user,
        'user_email': recipient_contacts.get('email', None),
        'user_sms': recipient_contacts.get('sms', None),
        'user_firstname': userfirstname or 'user',
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

def get_demo_template_path() -> Path:
    """Get the path where demo templates are stored"""
    try:
        # return files('tattler.templates').joinpath('.')
        return files('tattler.templates').joinpath('.')
    except TypeError:
        # python 3.9 behavior. Workaround by returning path
        return Path(__file__).parent.parent.joinpath('templates')

def get_template_mgr(event_scope: Optional[str]=None) -> TemplateMgr:
    """Return the TemplateMgr instance for base path or scope, from configuration or demo fallback.
    
    If 'TATTLER_TEMPLATE_BASE' setting is provided, construct TemplateMgr for it. Else construct
    TemplateMgr for embedded demo templates folder.

    :param event_scope:     Optional scope name to restrict template manager to.
    
    :return:                Instance of TemplateMgr rooted at the base templates directory, or potentially scoped directory."""
    base_path = getenv('TATTLER_TEMPLATE_BASE')
    if base_path:
        base_path = Path(base_path)
    else:
        # load embedded demo templates
        base_path = get_demo_template_path()
    if not event_scope:
        return TemplateMgr(base_path)
    if base_path.exists() and not base_path.joinpath(event_scope).exists():
        log.error("Scope '%s' under template dir '%s' does not exist.", event_scope, base_path)
        raise FileNotFoundError(f"Scope does not exist: '{event_scope}'")
    return TemplateMgr(base_path.joinpath(event_scope))

def get_validated_template_mgr(event_scope: str, event_name: str, vectors: Iterable[str]) -> TemplateMgr:
    """Verifies the availability of the event parameters at the requested template base and returns a template manager for it.
    
    :param base_path:       Path for which to contruct the template manager.
    :param event_scope:     Name of the scope where to search the event.
    :param event_name:      Name of the event to verify.
    
    :return:                Template manager to supply the template with the given parameters.
    """
    tman = get_template_mgr(event_scope)
    if event_name not in tman.available_events():
        log.error("Event does not exist: '%s' in scope '%s' (base = '%s'). Rejecting notification", event_name, event_scope, tman.base_path)
        raise ValueError(f"Event does not exist: '{event_name}' in scope '{event_scope}'")
    event_vectors = set(tman.available_vectors(event_name))
    if vectors is None:
        vectors = event_vectors
    active_vectors = set(vectors) & event_vectors
    if not active_vectors:
        msg = "None of the requested vectors %s is available for event %s, which only supports %s. Returning error."
        params = (vectors, event_name, event_vectors)
        log.error(msg, *params)
        raise ValueError(msg % params)
    return tman, active_vectors

def check_templates_health() -> Path:
    """Check validity and return path to templates from environment settings, or default.
    
    If envvar TATTLER_TEMPLATE_BASE is set, use that.
    Else, use the internal path to native demo templates.
    """
    try:
        tman = get_template_mgr()
        tman.validate_templates()
    except FileNotFoundError as err:
        log.error("Template directory failed health check: %s. Fix this before notification requests come in. I do real-time loading, so I'll keep going now.", err)
        raise
    except ValueError as err:
        log.error("Error! Some templates in %s appear malformed, which will prevent their delivery: %s", tman.base_path, err)
        raise
    try:
        tman.validate_configuration()
    except ValueError as err:
        log.error("Issues found in configuration: %s. Correct those and restart", err)
        raise
    return tman.base_path

def send_notification_user_vectors(recipient_user, vectors, event_scope, event_name, context=None, correlationId=None, mode='debug') -> Iterable[str]:
    """Send a notification to a recipient across a set of vectors, and return the list of vectors which succeeded"""
    context = context or {}
    mode = mode or 'debug'
    if mode not in sendable.modes:
        raise ValueError(f"Invalid mode {mode}. Expected one of {sendable.modes}")
    tman, vectors = get_validated_template_mgr(event_scope, event_name, vectors)
    log.debug("<-Request to send #%s to %s (cid=%s)", recipient_user, vectors, correlationId)
    user_contacts = pluginloader.lookup_contacts(recipient_user)
    if user_contacts is None:
        log.warning("Recipient unknown '%s'. Aborting notification.", recipient_user)
        raise ValueError(f"Recipient unknown '{recipient_user}'. Aborting notification.")
    log.debug("Contacts for recipient %s are: %s", recipient_user, user_contacts)
    user_available_vectors = {vname for vname in vectors if user_contacts.get(vname, None) is not None}
    usrlang = user_contacts.get('language', None)
    log.info("Recipient %s is reachable over %d vectors of the %d requested: %s", recipient_user, len(user_available_vectors), len(vectors), user_available_vectors)
    retval = []
    for vname in user_available_vectors:
        if usrlang is not None:
            log.warning("User language set to non-default '%s', but tattler community edition doesn't do multilingual, so I'll send the default language", usrlang)
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
        log.info("Client requests mode='%s' while master mode='%s' => capping at '%s'.", requested_mode, master_mode, master_mode)
        return master_mode
    return requested_mode

def replace_time_values(obj):
    """Transform any time value in an object into a serializable form"""
    if isinstance(obj, dict):
        return {k:replace_time_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_time_values(v) for v in obj]
    elif isinstance(obj, str):
        # date?
        for t in [date, datetime]:
            try:
                return t.fromisoformat(obj)
            except ValueError:
                pass
    return obj

def obfuscate(data: str, key: Optional[str]=None) -> bytes:
    """Return a representation of data obfuscated in a reversable way.
    
    :param data:        Raw data to obfuscate.
    :param key:         Optional key to use for decryption. If omitted, a key valid for one day will be used.
    :return:            The obfuscated form of the string.
    """
    key = key or datetime.today().strftime('%Y%m%d')
    outvals = []
    for i, c in enumerate(key + data):
        ordval = ord(c)
        ordkey = ord(key[i % len(key)])
        outvals.append(ordval + ordkey)
    outstr = ','.join([str(i) for i in outvals])
    return base64.b64encode(outstr.encode())

def unobfuscate(data: bytes, key: Optional[str]=None) -> str:
    """Return a data reversed from obfuscation.
    
    :param data:        Raw data to decrypt.
    :param key:         Optional key to use for decryption. If omitted, a key valid for one day will be used.
    :return:            The value of the string decrypted.
    :raises ValueError: If the key could not successfully decrypt the original data.
    """
    key = key or datetime.today().strftime('%Y%m%d')
    outstr = ''
    try:
        indata = base64.b64decode(data).decode().split(',')
        invals  = [int(i) for i in indata]
    except (UnicodeDecodeError, binascii.Error, ValueError) as err:
        raise ValueError("Cannot decode data") from err
    for i, num in enumerate(invals):
        lookup_key = num - ord(key[i % len(key)])
        outstr += chr(lookup_key)
    if not outstr.startswith(key):
        raise ValueError("Key could not successfully unobfuscate string with given key.")
    return outstr[len(key):]
