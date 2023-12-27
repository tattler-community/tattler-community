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


class ContextTattlerPlugin(TattlerPlugin):
    """Base class that every context plugin inherits from."""

    plugin_category = 'context'

    def processing_required(self, context: ContextType) -> bool:
        """Returns whether this plugin should be called, based on the context."""
        return True

    def process(self, context: ContextType) -> ContextType:
        """Actually run the plugin, and return a new, potentially modified context."""
        return context


class AddressbookPlugin(TattlerPlugin):
    """Base class for AddressBook plug-ins.
    
    You can either implement the attributes() method, returning a dictionary
    with the relevant contacts -- or implement methods for individual attributes: email(),
    mobile(), first_name() etc.

    The default implementation for attributes() calls the individual email(), mobile() etc methods,
    so do not implement the latter ones by calling attributes(), as that would cause an infinite
    loop.

    Unknown contacts should be None.
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

    def attributes(self, recipient_id: str, role: Optional[str]=None) -> Mapping[str, Optional[str]]:
        """Return all attributes for a user at once.

        You may either implement this method, or implement each of the alternative methods to look up
        individual contacts -- such as email().

        This method's default implementation simply collects the attributes by calling the respective
        individual, e.g. 'email': self.email().

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
            'account_type': self.account_type(recipient_id, role),
            'first_name': self.first_name(recipient_id, role),
        }
        res['sms'] = res['mobile']
        return res

    def recipient_exists(self, recipient_id: str) -> bool:
        """Returns whether a user exists at all.
        
        :param recipient_id:    Unique identifier for the intended recipient, e.g. user ID from IAM system.
        :param role:            Intended role within the account to get address for, e.g. 'billing' or 'technical'.

        :return:                Whether an account exists for the recipient.
        """
        return any(self.attributes(recipient_id).values())


_plugin_classes = [ContextTattlerPlugin, AddressbookPlugin]

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
    """
    candidate_modules = get_plugin_names(paths)
    loaded_modules = {}
    for name, finder in candidate_modules.items():
        modspec = finder.find_spec(name)
        loaded_modules[name] = importlib.util.module_from_spec(modspec)
        modspec.loader.exec_module(loaded_modules[name])
    return loaded_modules


def load_plugins(candidate_modules: Mapping[str, Any]) -> Mapping[str, TattlerPlugin]:
    """Locate and setup the classes - within the candidate modules - that are usable as context processors."""
    enabled_processor_classes = {}
    for modname, modobj in candidate_modules.items():
        for membername, processor_candidate in inspect.getmembers(modobj, inspect.isclass):
            pclass = plugin_category(membername, processor_candidate)
            if pclass is None:
                log.debug("Ignoring class %s (%s) from module %s which is not a subclass of %s", membername, processor_candidate, modname, TattlerPlugin)
            else:
                log.info("Loading plugin %s (%s) from module %s", membername, processor_candidate, modname)
                try:
                    cand = processor_candidate()
                    cand.setup()
                    if pclass not in enabled_processor_classes:
                        enabled_processor_classes[pclass] = {}
                    enabled_processor_classes[pclass][membername] = cand
                except Exception as err:
                    log.exception("Plugin %s (in %s) failed to setup. Skipping to enable it. %s", membername, modname, err)
    return enabled_processor_classes


def init(paths: Iterable[str]) -> None:
    """Initialize the plugin subsystem and load all available plugins."""
    global loaded_plugins
    plugcand = load_candidate_modules(paths)
    loaded_plugins = load_plugins(plugcand)


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
