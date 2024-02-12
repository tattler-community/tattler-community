"""Definitions to declare Tattler plugins and logic to load them"""

import importlib
from importlib.abc import MetaPathFinder
import pkgutil
import logging
from datetime import datetime
import os
import inspect
from typing import Mapping, Any, Iterable, Optional

ContextType = Mapping[str, Any]

plugins_suffix = '_tattler_plugin'

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)


class TattlerPlugin:
    """Category of plugin for every subclass to define."""
    plugin_category = None

    """Base class for any tattler plugin."""
    def setup(self) -> None:
        """Perform a one-off initialization of this plugin, e.g. connect to DB.
        
        Overriding this method is optional. If a plugin's setup() method raises an exception,
        the plugin is not activated.
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



def plugin_category(symbolname: str, symbolclass: type) -> Optional[str]:
    """Return whether a symbol is a valid plugin."""
    if symbolclass in _plugin_classes + [TattlerPlugin]:
        return None
    for pclass in _plugin_classes:
        if issubclass(symbolclass, pclass):
            log.debug("Ignoring Symbol '%s' (%s) as it does not inherit from %s", symbolname, symbolclass, ContextTattlerPlugin)
            return pclass.plugin_category
    return None


def get_plugin_names(paths: Iterable[str]) -> Mapping[str, MetaPathFinder]:
    importlib.invalidate_caches()
    return {name: finder for finder, name, _ in pkgutil.iter_modules(paths) if name.endswith(plugins_suffix)}

def load_candidate_modules(paths: Iterable[str]) -> Mapping[str, Any]:
    """Find and import modules that match Tattler plugins naming requirements.
    
    The modules are only 'candidates': a later stage will find classes within them
    that implement the required interface to be processors.

    :param paths:   List of filesystem paths to search for plug-in definitions.

    :return:        Dictionary {name: module} listing modules that may hold classes implementing plug-ins.
    """
    candidate_modules = get_plugin_names(paths)
    loaded_modules = {}
    for name, finder in candidate_modules.items():
        modspec = finder.find_spec(name)
        loaded_modules[name] = importlib.util.module_from_spec(modspec)
        modspec.loader.exec_module(loaded_modules[name])
    return loaded_modules

def check_sanity(classname: str, modname: str, pluginclass: type) -> bool:
    """Check whether a candidate plug-in class is safe to load as a plug-in.
    
    :param classname:       Name of the class being sanity-checked.
    :param modname:         Name of the file (module) that provided the implementation of the candidate class.
    :param pluginclass:     Class of the candidate plug-in.
    
    :return:                Whether the class may be loaded as a plug-in."""
    if issubclass(pluginclass, ContextTattlerPlugin):
        log.warning("""Deprecation warning: plug-in candidate '%s' (%s) in module '%s' implements class 'ContextTattlerPlugin' instead of 'ContextPlugin' (renamed in 1.2.0)""", classname, pluginclass, modname)
    return True

def load_plugins(candidate_modules: Mapping[str, Any]) -> Mapping[str, Mapping[str, TattlerPlugin]]:
    """Locate and setup the classes - within the candidate modules - that are usable as context processors.
    
    :param candidate_modules:   Dictionary {name: module} listing modules that may hold classes implementing plug-ins.

    :return:        Dictionary {typename: {pluginname: class}} whose keys are plugin types in {'context', 'addressbook'}, and values are dictionaries mapping plug-in names to their class.
    """
    enabled_processor_classes = {}
    # sort classes by name, so the order of initialization and execution are deterministic and externally-controllable
    candidate_classes = [(classname, [modname, classcand]) for modname, modobj in candidate_modules.items() for classname, classcand in inspect.getmembers(modobj, inspect.isclass)]
    candidate_classes.sort(key=lambda x: x[0])
    for classname, classitems in candidate_classes:
        modname, processor_candidate = classitems
        pclass = plugin_category(classname, processor_candidate)
        if pclass is None:
            log.debug("Ignoring class %s (%s) from module %s which is not a subclass of %s", classname, processor_candidate, modname, TattlerPlugin)
        else:
            if not check_sanity(classname, modname, processor_candidate):
                log.warning("Candidate plug-in class '%s' (%s) from module %s failed sanity check. Will not load it.", classname, processor_candidate, modname)
                continue
            log.info("Loading plugin %s (%s) from module %s", classname, processor_candidate, modname)
            try:
                cand = processor_candidate()
                cand.setup()
                if pclass not in enabled_processor_classes:
                    enabled_processor_classes[pclass] = {}
                enabled_processor_classes[pclass][classname] = cand
            except Exception as err:
                log.exception("Plugin %s (in %s) failed to setup. Skipping to enable it. %s", classname, modname, err)
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

def process_context(context: ContextType) -> ContextType:
    """Process the context through pipelines of all plugins loaded, and return resulting context."""
    context_plugins = loaded_plugins.get('context', {})
    for i, (pname, proc) in enumerate(context_plugins.items()):
        log.info("Processing context through context plugin #%d '%s'", i, pname)
        try:
            preq = proc.processing_required(context)
        except:
            log.exception("Plugin %s failed checking if processing_required():", pname)
            continue
        if not preq:
            log.info("Skipping plugin %s as its processing_required() was False", pname)
            log.debug("PS: Context checked was: %s", context)
            continue
        log.info("Processing context through plugin %s", pname)
        t0 = datetime.now()
        try:
            context = proc.process(context)
            log.info("Context after plugin %s (in %s): %s", pname, datetime.now()-t0, context)
        except:
            log.exception("Plugin %s failed process():", pname)
    return context


def lookup_contacts(recipient_id: str, role: Optional[str]=None, vectors: Optional[Iterable[str]]=None) -> Mapping[str, Optional[str]]:
    """Lookup an attribute of a given user in all addressbook plugins.

    @role  [str|None]  Role to look up for this user, e.g. 'billing', 'technical', 'administrative'.
    """
    addressbook_plugins = loaded_plugins.get('addressbook', {})
    for i, (pname, proc) in enumerate(addressbook_plugins.items()):
        log.info("Looking up recipient %s with addressbook plugin #%d '%s'", recipient_id, i, pname)
        try:
            if not proc.recipient_exists(recipient_id):
                log.debug("Plugin %s doesn't know recipient %s. Moving on to next plugin.", pname, recipient_id)
                continue
        except Exception:
            log.exception("Plugin #%d '%s' raised exception in recipient_exists(). Moving on to next. Error was:", i, pname)
            continue
        try:
            attrs = proc.attributes(recipient_id)
        except Exception:
            log.exception("Plugin #%d '%s' raised exception in attributes(). Moving on to next. Error was:", i, pname)
            continue
        if attrs is not None:
            return attrs
    log.warning("No contacts could be found for recipient '%s'.", recipient_id)
    return None
