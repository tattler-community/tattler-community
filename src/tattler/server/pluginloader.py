"""Definitions to declare Tattler plugins and logic to load them"""

import importlib.util
import logging
from datetime import datetime
from pathlib import Path
import os
import inspect
from typing import Mapping, Any, Iterable, Optional

ContextType = Mapping[str, Any]

plugins_suffix = '_tattler_plugin'

# paths tattler ships plug-ins in, scanned in addition to any user-supplied TATTLER_PLUGIN_PATH
native_plugin_paths = [
    Path(__file__).parent / 'plugins',
    Path(__file__).parent / 'sendable' / 'backends',
]

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)


class PluginNotConfigured(ValueError):
    """Raised by a plugin's setup() when it is deliberately left unconfigured, so it is skipped without error."""


class TattlerPlugin:
    """Category of plugin for every subclass to define."""
    plugin_category = None

    """Base class for any tattler plugin."""
    def setup(self) -> None:
        """Perform a one-off initialization of this plugin, e.g. connect to DB.

        Overriding this method is optional. If a plugin's setup() method raises an exception,
        the plugin is not activated. Raise :class:`PluginNotConfigured` to signal that the plugin
        is simply not configured for use, so it is skipped without reporting an error.
        """
        pass


class ContextPlugin(TattlerPlugin):
    """Base class for Context plug-ins, which extend or override context variables for templates.

    A Context plug-in may choose to indicate whether it should be run
    -- for each notification request -- by implementing the :meth:`processing_required` method,
    which otherwise defaults to True.
    
    This enables resource-intensive plug-ins to only "fire" when necessary, e.g. based on
    the event being notified, the recipient, or more.

    If multiple context plug-ins are provided, tattler "pipelines" them, i.e. it passes the
    its native context to the first, and the resulting context to each subsequent context plug-in.
       
    .. versionadded:: 1.2.0
        This was named ``ContextTattlerPlugin`` in tattler versions up to 1.1.1,
        and was renamed in version 1.2.0 for simplicity and symmetry with :class:`AddressbookPlugin`.

        Version 1.2.0 retains name :class:`ContextTattlerPlugin` as an alias to this class
        for backward compatibility, but tattler will produce a deprecation
        warning at runtime for plug-ins that still inherit from ``ContextTattlerPlugin``.
    """

    plugin_category = 'context'

    def processing_required(self, context: ContextType) -> bool:
        """Return whether this plugin should be called, based on the context.

        Implementing this method is optional, and defaults to ``True`` otherwise.
         
        Implement this only if you're writing a very resource-intensive context plug-in.
        
        In most scenarios, the rate of notifications is low enough to have
        the risk and complications of introducing this dynamic behavior vastly exceed
        the benefit of the spared CPU cycles.

        If you do implement this, try to keep your logic simple and based on
        deterministic variables (like the scope name or event name) rather than
        more complex, less predictable data like the presence of some variable
        from previous plug-ins.

        :param context:     The latest context resulting from the previous plug-in, or tattler's native context for the first-running context plug-in.

        :return:            Whether :meth:`process` should be called for this plug-in.
        """
        return True

    def process(self, context: ContextType) -> ContextType:
        """Run the plug-in to generate new context data.

        The latest (previous) context is passed as input to this method, allowing
        the method to add, change or remove variables from it.

        Email attachments may be supplied via the reserved ``_attachments``
        key, a dict whose keys disambiguate inline from regular by format:
        a key containing ``@`` is the Content-ID of an inline image
        (referenced from HTML as ``cid:<key>``); content type is auto-detected
        from the bytes (PNG, JPEG, GIF, WebP, SVG). A key without ``@`` is
        the filename of a regular attachment, and the key drives content type.

        The same shape is used by HTTP callers, except plugins pass raw
        ``bytes`` via ``content_bytes`` instead of base64 via ``content_b64``.

        Plugins are pipelined: a later plugin sees the attachments accumulated
        by earlier plugins and may extend the dict. To avoid mutating upstream
        state, copy before adding::

            attachments = dict(context.get('_attachments', {}))
            attachments['logo@local'] = {'content_bytes': b'...'}      # inline
            attachments['invoice.pdf'] = {'content_bytes': b'...'}     # regular
            context['_attachments'] = attachments

        :param context:     The latest context resulting from the previous plug-in, or tattler's native context for the first-running context plug-in.
        :return:            The generated context to either feed to the template, or to the next context plug-in in the chain.
        """
        return context


class ContextTattlerPlugin(ContextPlugin):
    """Compatibility alias to class ContextPlugin, renamed in Tattler version 1.1.1.
    
    .. deprecated:: 1.2.0
        Use class :class:`ContextPlugin` instead. Name :class:`ContextTattlerPlugin` is
        retained as an alias for backward compatibility, but tattler will log a deprecation
        warning at runtime for plug-ins still inheriting from this name.
    """

class AddressbookPlugin(TattlerPlugin):
    """Base class for AddressBook plug-ins.
    
    You can either implement the :meth:`attributes` method, returning a dictionary
    with the relevant contacts -- or implement methods for individual attributes: :meth:`email`,
    :meth:`mobile`, meth:`first_name` etc.

    The default implementation for :meth:`attributes` calls the individual :meth:`email`,
    :meth:`mobile` etc methods, so do not implement the latter ones by calling meth:`attributes`,
    as that would cause an infinite loop.

    Unknown contacts should be ``None``.
    """

    plugin_category = 'addressbook'

    def email(self, recipient_id: str, role: Optional[str]=None) -> Optional[str]:
        """Return the email address associated with a user identifier, if known.
        
        :param recipient_id: Unique identifier for the intended recipient, e.g. user ID from IAM system.
        :param role: intended role within the account to get address for, e.g. 'billing' or 'technical'.
        :return: email address to deliver to, or None if unknown."""
        return None

    def mobile(self, recipient_id: str, role: Optional[str]=None) -> Optional[str]:
        """Return the mobile number associated with a user identifier, if known.
        
        :param recipient_id:    Unique identifier for the intended recipient, e.g. user ID from IAM system.
        :param role:            Intended role within the account to get address for, e.g. 'billing' or 'technical'.
        :return:                Mobile number to deliver to, or None if unknown."""
        return None

    def telegram(self, recipient_id: str, role: Optional[str]=None) -> Optional[str]:
        """Return the telegram ID for the recipient, if known.

        Nota bene: The Telegram platform requires the user to have contacted the bot before
        the bot is allowed to message the user.

        :param recipient_id:    Unique identifier for the intended recipient, e.g. user ID from IAM system.
        :param role:            Intended role within the account to get address for, e.g. 'billing' or 'technical'.
        :return:                Telegram chat id to deliver to, or None if unknown."""
        return None

    def account_type(self, recipient_id: str, role: Optional[str]=None) -> Optional[str]:
        """Return the type of account that the user is on, if known and relevant.

        :param recipient_id:    Unique identifier for the intended recipient, e.g. user ID from IAM system.
        :param role:            Intended role within the account to get address for, e.g. 'billing' or 'technical'.
        :return:                A descriptor of the account type the user is on (e.g. "free", "paid", "planX"), or None if unknown."""
        return None
    
    def first_name(self, recipient_id: str, role: Optional[str]=None) -> Optional[str]:
        """Return the user's first name, if known.

        :param recipient_id:    Unique identifier for the intended recipient, e.g. user ID from IAM system.
        :param role:            Intended role within the account to get address for, e.g. 'billing' or 'technical'.
        :return:                User's first name (e.g. "Paul"), or None if unknown."""
        return None

    def language(self, recipient_id: str, role: Optional[str]=None) -> Optional[str]:
        """Return the user's language, if known; only supported in tattler enterprise edition.

        :param recipient_id:    Unique identifier for the intended recipient, e.g. user ID from IAM system.
        :param role:            Intended role within the account to get address for, e.g. 'billing' or 'technical'.
        :return:                Language code requested by the user (e.g. "en" or "en_US" -- consult with template designer), or None if unknown."""
        return None

    def attributes(self, recipient_id: str, role: Optional[str]=None) -> Mapping[str, Optional[str]]:
        """Return all attributes for a user at once.

        You may either implement this method, or implement each of the alternative methods to look up
        individual contacts -- such as :meth:`email`.

        This method's default implementation simply collects the attributes by calling the respective
        individual, e.g. 'email': ``self.email()``. A key should be returned for every required vector
        name. The default implementation of this method simply collects the return values of the individual
        methods, such as {'mobile': self.mobile() }, and then adds aliases for the vector names, such as
        {'sms': ='mobile', 'whatsapp': ='mobile'}.

        Implementing this method is more efficient if your lookup returns all user contacts in one call,
        e.g. because they are all in one database. Implementing the individual contact methods may help
        to keep your logic simpler, if the look ups for each method actually involve different logic.

        This is the method ultimately called by tattler.
        
        :param recipient_id:    Unique identifier for the intended recipient, e.g. user ID from IAM system.
        :param role:            Intended role within the account to get address for, e.g. 'billing' or 'technical'.

        :return:                Map of known contact types and either their value, or None if unknown, for at least {'email', 'mobile', 'account_type', 'first_name'}."""
        res = {
            'email': self.email(recipient_id, role),
            'mobile': self.mobile(recipient_id, role),
            'telegram': self.telegram(recipient_id, role),
            'account_type': self.account_type(recipient_id, role),
            'first_name': self.first_name(recipient_id, role),
            'language': self.language(recipient_id, role),
        }
        res['sms'] = res['mobile']
        res['whatsapp'] = res['mobile']
        return res

    def recipient_exists(self, recipient_id: str) -> bool:
        """Returns whether a user exists at all.
        
        :param recipient_id:    Unique identifier for the intended recipient, e.g. user ID from IAM system.
        :param role:            Intended role within the account to get address for, e.g. 'billing' or 'technical'.

        :return:                Whether an account exists for the recipient.
        """
        return any(self.attributes(recipient_id).values())


_plugin_classes = [ContextPlugin, ContextTattlerPlugin, AddressbookPlugin]

loaded_plugins = {}

# {category: {classname: (class, error message)}} for candidates that failed setup(), so
# callers needing every candidate's status (e.g. reporting "no backend configured") can retrieve why.
loaded_plugin_errors = {}


def register_plugin_class(baseclass: type) -> None:
    """Register an additional plugin base class, so its subclasses are recognized as plug-ins.

    This lets other tattler modules define plugin categories without this module having
    to know them, avoiding circular imports.

    :param baseclass:   TattlerPlugin subclass defining the category, e.g. an SMS backend interface."""
    if baseclass not in _plugin_classes:
        _plugin_classes.append(baseclass)



def plugin_category(symbolname: str, symbolclass: type) -> Optional[str]:
    """Return whether a symbol is a valid plugin."""
    if symbolclass in _plugin_classes + [TattlerPlugin]:
        return None
    for pclass in _plugin_classes:
        if issubclass(symbolclass, pclass):
            log.debug("Ignoring Symbol '%s' (%s) as it does not inherit from %s", symbolname, symbolclass, ContextTattlerPlugin)
            return pclass.plugin_category
    return None


def load_candidate_modules(paths: Iterable[str]) -> Mapping[str, Any]:
    """Find and import modules that match Tattler plugins naming requirements.

    The modules are only 'candidates': a later stage will find classes within them
    that implement the required interface to be processors.

    :param paths:   List of filesystem paths to search for plug-in definitions.

    :return:        Dictionary {name: module} listing modules that may hold classes implementing plug-ins.
    """
    loaded_modules = {}
    for path in paths:
        path = Path(path)
        if not path.is_dir():
            log.debug("Skipping plugin path '%s': not a directory.", path)
            continue
        # plug-ins that live within this package (e.g. sendable/backends) are imported by their
        # dotted name like any other submodule, keeping a single canonical module/class object
        # (needed e.g. for tests to mock.patch() their dependencies); third-party plug-ins
        # (TATTLER_PLUGIN_PATH) live outside the package and have no dotted name, so they're
        # loaded directly from file.
        dotted_pkg = _dotted_module_name(path)
        log.debug("Scanning plugin path '%s' (dotted package: %s)", path, dotted_pkg or 'none, loading from file')
        for moddir in sorted(p for p in path.glob(f'*{plugins_suffix}') if p.is_dir()):
            log.warning("Ignoring plugin folder '%s': plugins must be single files named '*%s.py'.", moddir, plugins_suffix)
        for modfile in sorted(path.glob(f'*{plugins_suffix}.py')):
            assert modfile.stem not in loaded_modules, f"Plugin module name collision: '{modfile.stem}' (in '{path}') is provided by multiple plugin paths."
            if dotted_pkg:
                log.info("Importing candidate plugin module '%s.%s'", dotted_pkg, modfile.stem)
                loaded_modules[modfile.stem] = importlib.import_module(f'{dotted_pkg}.{modfile.stem}')
            else:
                log.info("Loading candidate plugin module '%s' from file '%s'", modfile.stem, modfile)
                modspec = importlib.util.spec_from_file_location(modfile.stem, modfile)
                loaded_modules[modfile.stem] = importlib.util.module_from_spec(modspec)
                modspec.loader.exec_module(loaded_modules[modfile.stem])
    log.debug("Found %d candidate plugin module(s): %s", len(loaded_modules), sorted(loaded_modules))
    return loaded_modules


def _dotted_module_name(path: Path) -> Optional[str]:
    """Return the dotted package name of a directory within this package, or None if outside it.

    :param path:    Directory to name, e.g. .../tattler/server/sendable/backends.

    :return:        Dotted name, e.g. 'tattler.server.sendable.backends', or None if path isn't under it."""
    try:
        rel = path.resolve().relative_to(Path(__file__).resolve().parent.parent.parent)
    except ValueError:
        log.debug("Plugin path '%s' is outside this package; treating it as a third-party path.", path)
        return None
    return '.'.join(rel.parts)

def check_sanity(classname: str, modname: str, pluginclass: type) -> bool:
    """Check whether a candidate plug-in class is safe to load as a plug-in.
    
    :param classname:       Name of the class being sanity-checked.
    :param modname:         Name of the file (module) that provided the implementation of the candidate class.
    :param pluginclass:     Class of the candidate plug-in.
    
    :return:                Whether the class may be loaded as a plug-in."""
    if issubclass(pluginclass, ContextTattlerPlugin):
        log.warning("""Deprecation warning: plug-in candidate '%s' (%s) in module '%s' implements class 'ContextTattlerPlugin' instead of 'ContextPlugin' (renamed in 1.2.0)""", classname, pluginclass, modname)
    return issubclass(pluginclass, TattlerPlugin)

def load_plugins(candidate_modules: Mapping[str, Any]) -> Mapping[str, Mapping[str, TattlerPlugin]]:
    """Locate and setup the classes - within the candidate modules - that are usable as context processors.
    
    :param candidate_modules:   Dictionary {name: module} listing modules that may hold classes implementing plug-ins.

    :return:        Dictionary {typename: {pluginname: class}} whose keys are plugin types in {'context', 'addressbook'}, and values are dictionaries mapping plug-in names to their class.
    """
    global loaded_plugin_errors
    loaded_plugin_errors = {}
    enabled_processor_classes = {}
    # {(defining module, classname): (classname, modname, class)}: modules importing the same class (e.g. a shared
    # base) expose it multiple times, possibly as distinct objects if loaded twice, so consider each definition once
    candidate_classes: dict[tuple[str, str], tuple[str, str, type]] = {}
    for modname, modobj in candidate_modules.items():
        members = inspect.getmembers(modobj, inspect.isclass)
        log.debug("Members of %s: %s", modname, members)
        for classname, classcand in members:
            candidate_classes.setdefault((classcand.__module__, classname), (classname, modname, classcand))
    # sort classes by name, so the order of initialization and execution are deterministic and externally-controllable
    for classname, modname, processor_candidate in sorted(candidate_classes.values(), key=lambda x: x[0]):
        pclass = plugin_category(classname, processor_candidate)
        if pclass is None:
            log.debug("Ignoring class %s (%s) from module %s which is not a subclass of %s", classname, processor_candidate, modname, TattlerPlugin)
        else:
            if not check_sanity(classname, modname, processor_candidate):
                log.warning("Candidate plug-in class '%s' (%s) from module %s failed sanity check. Will not load it.", classname, processor_candidate, modname)
                continue
            log.info("Loading plugin %s (%s) from module %s", classname, processor_candidate, modname)
            assert classname not in enabled_processor_classes.get(pclass, {}), f"Plugin class name collision: '{classname}' (in module '{modname}') is declared by multiple plugin modules."
            try:
                cand = processor_candidate()
                cand.setup()
                enabled_processor_classes.setdefault(pclass, {})[classname] = cand
            except PluginNotConfigured as err:
                log.info("Plugin %s (in %s) is not configured, so not enabling it: %s", classname, modname, err)
                loaded_plugin_errors.setdefault(pclass, {})[classname] = (processor_candidate, str(err))
            except Exception as err:
                log.error("Plugin %s (in %s) failed to setup, so not enabling it. Error %s: %s", classname, modname, type(err), err)
                loaded_plugin_errors.setdefault(pclass, {})[classname] = (processor_candidate, str(err))
    return enabled_processor_classes

def load_plugins_from_modules(paths: Iterable[str]) -> Mapping[str, Mapping[str, TattlerPlugin]]:
    """Scan paths for plug-in implementations, and load the suitable candidates.
    
    :param paths:   List of filesystem paths to search for plug-in definitions.
    
    :return:        Dictionary {typename: {pluginname: class}} whose keys are plugin types in {'context', 'addressbook'}, and values are dictionaries mapping plug-in names to their class.
    """
    plugcand = load_candidate_modules(paths)
    return load_plugins(plugcand)

def init(paths: Iterable[str]) -> None:
    """Initialize the plugin subsystem and load all available plugins.
    
    :param paths:   List of filesystem paths to search for plug-in definitions."""
    global loaded_plugins
    loaded_plugins = load_plugins_from_modules(paths)

class ContextProcessingError(Exception):
    """Raised when a context plugin failed to process the context, e.g. due to backend errors.

    Notifications are aborted in this case, since sending a notification with incomplete or
    wrong data is worse than sending none."""


def process_context(context: ContextType) -> ContextType:
    """Process the context through pipelines of all plugins loaded, and return resulting context.

    :raise ContextProcessingError:  if any context plugin raised an error or returned an invalid
                                     context, so the notification should be aborted rather than
                                     sent with incomplete data.
    """
    context_plugins = loaded_plugins.get('context', {})
    for i, (pname, proc) in enumerate(context_plugins.items()):
        log.info("Processing context through context plugin #%d '%s'", i, pname)
        try:
            preq = proc.processing_required(context)
        except Exception as err:
            log.exception("Plugin #%d '%s' raised exception in processing_required() (recipient='%s', corrId=%s). Aborting notification. Error was:", i, pname, context.get('user_id'), context.get('correlation_id'))
            raise ContextProcessingError(f"Context plugin '{pname}' failed in processing_required().") from err
        if not preq:
            log.info("Skipping plugin %s as its processing_required() was False", pname)
            log.debug("PS: Context checked was: %s", context)
            continue
        log.info("Processing context through plugin %s", pname)
        t0 = datetime.now()
        try:
            newcontext = proc.process(context)
        except Exception as err:
            log.exception("Plugin #%d '%s' raised exception in process() (recipient='%s', corrId=%s). Aborting notification. Error was:", i, pname, context.get('user_id'), context.get('correlation_id'))
            raise ContextProcessingError(f"Context plugin '{pname}' failed in process().") from err
        if not isinstance(newcontext, Mapping):
            log.error("Plugin #%d '%s' returned invalid context %s instead of a mapping (recipient='%s', corrId=%s). Aborting notification.", i, pname, type(newcontext), context.get('user_id'), context.get('correlation_id'))
            raise ContextProcessingError(f"Context plugin '{pname}' returned invalid context of type {type(newcontext)}.")
        context = newcontext
        log.info("Context after plugin %s (in %s): %s", pname, datetime.now()-t0, context)
    return context


class AddressbookLookupError(Exception):
    """Raised when no addressbook plugin could determine whether a recipient exists, due to backend errors.

    This is distinct from a recipient being genuinely unknown: it signals that the lookup itself
    failed (e.g. a database being unreachable), rather than the addressbook plugins cleanly reporting
    that the recipient does not exist.
    """


def lookup_contacts(recipient_id: str, role: Optional[str]=None, vectors: Optional[Iterable[str]]=None) -> Mapping[str, Optional[str]]:
    """Lookup an attribute of a given user in all addressbook plugins.

    @role  [str|None]  Role to look up for this user, e.g. 'billing', 'technical', 'administrative'.

    :raise AddressbookLookupError:  if every addressbook plugin raised an error, so the recipient's
                                     existence could not be determined (as opposed to being cleanly
                                     reported as unknown).
    """
    addressbook_plugins = loaded_plugins.get('addressbook', {})
    had_errors = False
    for i, (pname, proc) in enumerate(addressbook_plugins.items()):
        log.info("Looking up recipient %s with addressbook plugin #%d '%s'", recipient_id, i, pname)
        try:
            if not proc.recipient_exists(recipient_id):
                log.debug("Plugin %s doesn't know recipient %s. Moving on to next plugin.", pname, recipient_id)
                continue
        except Exception:
            log.exception("Plugin #%d '%s' raised exception in recipient_exists() for recipient '%s'. Moving on to next. Error was:", i, pname, recipient_id)
            had_errors = True
            continue
        try:
            attrs = proc.attributes(recipient_id)
        except Exception:
            log.exception("Plugin #%d '%s' raised exception in attributes() for recipient '%s'. Moving on to next. Error was:", i, pname, recipient_id)
            had_errors = True
            continue
        if attrs is not None:
            return attrs
    if had_errors:
        log.error("Could not determine contacts for recipient '%s': every addressbook plugin consulted raised an error.", recipient_id)
        raise AddressbookLookupError(f"Could not look up recipient '{recipient_id}': addressbook plugin(s) failed.")
    log.warning("No contacts could be found for recipient '%s'.", recipient_id)
    return None
