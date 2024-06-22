"""The abstract class parent to any message that can be delivered"""

import os
import os.path
import logging
import uuid
from pathlib import Path
from typing import Iterable, Mapping, Optional, Any, Union

from . import TemplateProcessor
from . import Blacklist

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)

_default_template_base: Path = os.getenv('TATTLER_TEMPLATE_BASE', ".")

default_mode = 'production'

def getenv(name, default=None):
    """getenv wrapper for mocking in testing"""
    return os.getenv(name, default)


class Sendable:
    """An template message that can be bound and sent."""

    # a dictionary of variable names required for the sendable to operate. validate_configuration() will raise if any is missing or empty
    required_settings = {
        # name:     [required: bool, validator: Optional[callable]]
    }

    # backwards compatibility: look for additional filename aliases when one filename is required.
    # Override this in children that need to customize it
    filename_aliases = {
        'body.txt': ['body']
    }

    def __init__(self, event: str, recipients: Iterable[str], template_processor: type[TemplateProcessor]=TemplateProcessor, template_base: str=_default_template_base, debug_recipient: Optional[str]=None, language_code: Optional[str]=None):
        """Build an object which can be expanded into content and delivered through a vector.
        
        :param: event:              Event name to search among event templates database.
        :param recipients:          List of recipient addresses to send the notification to; format is vector-specific.
        :param template_processor:  Custom TemplateProcessor class to use to expand template into sendable bytes.
        :param template_base:       Path to the root directory of the event templates database.
        :param debug_recipient:     Address to deliver the notification to instead of (in addition to) actual recipient when in debug (staging) mode.
        :param language_code:       Language code of event to look up (only supported in tattler enterprise edition).
        """
        try:
            self.recipients = [self.validate_recipient(r) for r in recipients]
        except ValueError as err:
            raise ValueError(f"Invalid {self.vector()} recipient(s) '{recipients}': {str(err)}.") from err
        self.nid = str(uuid.uuid4())
        self.event_name = event
        self.language_code = None
        if language_code is not None:
            self.load_language(language_code)
        self.template_base = Path(template_base)
        self.template_processor: type[TemplateProcessor] = template_processor
        self.debug_recipient_val = debug_recipient

    def validate_recipient(self, recipient: str) -> str:
        """Return normalized recipient, or raise ValueError if invalid."""
        return recipient

    def validate_template(self) -> None:
        """Raise iff any required part is missing or a part is not well-formed.
        
        :raise ValueError:     when any part of the template is invalid; exception message describes what."""
        if 'body.txt' not in self._get_template_elements_standardized():
            raise ValueError("Required part 'body.txt' is missing.")

    @classmethod
    def sender(cls, recipient: Optional[str]=None) -> Optional[str]:
        """Return the configured sender ID for a given recipient.

        The sender id is looked up in envvar TATTLER_{vecname}_SENDER. It returns:
         - its value if one is provided
         - if multiple values are provided (,-separated), the most suitable value for the recipient.

        The algorithm is vector-dependent, so see vector documentation for more.

        :param recipient:   Recipient for which the sender should be found; or None for default sender.
        
        :return:            ID to send the message as for the given recipient, or None if no configuration available."""
        return getenv(f"TATTLER_{cls.vector().upper()}_SENDER", None)

    @classmethod
    def validate_configuration(cls) -> None:
        """Raise iff a configuration parameter is missing or invalid.
        
        :raise ValueError:     when any part of the configuration is invalid; exception message describes what."""
        bp = getenv('TATTLER_BLACKLIST_PATH')
        if bp is not None:
            try:
                Blacklist(from_filename=bp)
            except FileNotFoundError as err:
                raise ValueError(f"Blacklist setting TATTLER_BLACKLIST_PATH={bp} cannot be open.") from err
        for vname, vrequirement in cls.required_settings.items():
            vmandatory, vvalidator = vrequirement
            if getenv(vname) is None:
                if vmandatory:
                    raise ValueError(f"Required setting '{vname}' to deliver over {cls.vector()} is missing.")
            else:
                val = getenv(vname).strip()
                if vvalidator and not vvalidator(val):
                    raise ValueError(f"Setting '{vname}'='{val}' is malformed.")

    def setup(self) -> None:
        """Validate that the necessary configuration is available and usable, and prepare object accordingly; raise RuntimeError otherwise."""

    def load_language(self, language_code: Optional[str]=None) -> None:
        """Setup the sendable to operate with the given language.
        
        :param language_code:       Language code of event to look up (only supported in tattler enterprise edition).
        """
        log.warning("Multilingualism is only supported by tattler enterprise edition. Community edition does not support language '%s' and falls back to the default language. See https://docs.tattler.dev/templatedesigners/multilingualism.html and https://tattler.dev/#enterprise .", language_code)

    def _get_template_pathname(self, base: bool=False) -> Path:
        """Return the path to the root folder of the event template for the vector.
        
        :param base:    Whether to look up the template as a base template (under _base).
        
        :return:        The path where the template for the vector can be found."""
        if base:
            loc_candidates = [loc / '_base' / self.vector() for loc in [self.template_base, self.template_base.parent ]]
            for loc in loc_candidates:
                if loc.exists():
                    return loc
            raise ValueError(f"No 'base ' template exists for '{self.vector()}:{self.event()}:{self.language_code}' (tried candidates {loc_candidates}).")
        template_pathname = self.template_base / self.event() / self.vector()
        if not template_pathname.exists():
            raise ValueError(f"No template exists for '{self.vector()}:{self.event()}:{self.language_code}' (missing file: {template_pathname}).")
        return template_pathname

    def _get_template_raw_element(self, name: str, base: bool=False) -> str:
        """Return the content of a specific template element within the event template for the vector.
        
        :param name:        Name of the element to look up within the event template for this vector.
        :param base:        Whether to look up the element within the event template or the base template.

        :return:            Content of the requested element.
        """
        aliases = self.filename_aliases.get(name, [])
        for alias in [name] + aliases:
            fname = self._get_template_pathname(base) / alias
            log.debug("n%s: Looking up '%s' %stemplate part -> %s", self.nid, name, ('base ' if base else ''), fname)
            if fname.exists():
                if alias in aliases:
                    log.warning("Deprecation warning: Found template file named '%s'. Rename it to '%s' (since v2.0). The old naming scheme will no longer be recognized in v3.0.", alias, name)
                return fname.read_text(encoding='utf-8')
        # File not found. Have Path object itself raise exection
        return (self._get_template_pathname(base) / name).read_text('utf-8')

    def _get_template_elements(self, base: bool=False) -> Iterable[str]:
        """Return a list of available elements within the event template for the vector.
        
        :return:    List of element names available within the event template or base template."""
        dirname = self._get_template_pathname(base)
        return {fname for fname in os.listdir(dirname) if not fname.startswith('.') and os.path.isfile(dirname / fname)}

    def _get_template_elements_standardized(self) -> Iterable[str]:
        """Return a list of available elements, with their standard names replaced in case of aliases, e.g. body_plain -> body.txt.
        
        See :py:meth:`_get_template_elements`.

        :return:    List of element names available within the event template or base template, with aliased names replaced with the standard name."""
        names = self._get_template_elements()
        # replace aliases with standard names
        stdnames = []
        for name in names:
            found_alias_stdname = [stdname for stdname, aliases in self.filename_aliases.items() if name in aliases]
            stdnames.append(found_alias_stdname[0] if found_alias_stdname else name)
        return set(stdnames)

    def _get_content_element(self, element: str, context: Mapping[str, Any]) -> str:
        """Return the final display content by expanding the requested element with the given context."""
        template = self._get_template_raw_element(element)
        try:
            base_template = self._get_template_raw_element(element, True)
        except ValueError:
            base_template = None
            log.debug("n%s: No base template provided for '%s:%s'. Ignoring.", self.nid, self.event_name, self.vector())
        t: TemplateProcessor = self.template_processor(template, base_content=base_template)
        return t.expand(context)

    @classmethod
    def exists(cls, event: str, template_base: Union[str, Path]) -> bool:
        """Return whether an event is available for sending over the current vector under a template base."""
        template_base = Path(template_base)
        pth = template_base / event / cls.vector()
        return pth.exists()

    def __str__(self) -> str:
        return f"{self.vector()} for '{self.event()}' to '{self.recipients}'"

    def blacklist(self, filename: Optional[Union[str, Path]]=None) -> None:
        """Load a blacklist if filename provided, or disable it if not or empty."""
        if filename:
            self._bl = Blacklist(from_filename=filename)
            log.info("Loaded blacklist %s with %s entries.", filename, len(self._bl))
        else:
            self._bl = None

    def is_blacklisted(self, recipient: str) -> bool:
        """Check if a recipient is blacklisted in the currenly-loaded blacklist, if any; return False otherwise."""
        if getattr(self, '_bl', None):
            return self._bl.blacklisted(recipient.strip().lower())
        return False

    def event(self) -> str:
        """Return the event name for the current sendable"""
        return self.event_name

    @classmethod
    def vector(cls) -> str:
        """Return the vector name for a given sendable class."""
        return 'Sendable'

    def raw_content(self) -> str:
        """Return the raw content of the unexpanded template."""
        return self._get_template_raw_element("body.txt")

    def content(self, context: Mapping[str, Any]) -> str:
        """Return the content of the sendable."""
        templbody = self.raw_content()
        templ: TemplateProcessor = self.template_processor(templbody)
        return templ.expand(context).strip()
    
    def debug_recipient(self) -> str:
        """Return recipient to send to when in debug mode."""
        if self.debug_recipient_val is not None:
            return self.debug_recipient_val
        return getenv(f'TATTLER_DEBUG_RECIPIENT_{self.vector().upper()}', None)

    def supervisor_recipient(self) -> str:
        """Return recipient to copy all mail to, if required"""
        return getenv(f'TATTLER_SUPERVISOR_RECIPIENT_{self.vector().upper()}', None)

    def delivery_recipients(self, mode) -> Iterable[str]:
        """Return the set of recipients for the specific mode of operation"""
        if mode == 'debug':
            if not self.debug_recipient():
                log.warning("mode=%s but no TATTLER_DEBUG_RECIPIENT_%s variable set!", mode, self.vector().upper())
                return set()
            return {self.debug_recipient()}
        elif mode == 'staging':
            if not self.supervisor_recipient():
                log.warning("mode=%s but no TATTLER_SUPERVISOR_RECIPIENT_%s variable set!", mode, self.vector().upper())
                return set(self.recipients)
            return set(self.recipients + [self.supervisor_recipient()])
        # production
        return set(self.recipients)

    def do_send(self, recipients: Iterable[str], context: Mapping[str, Any], priority: Optional[int]=None) -> None:
        """Concretely send the message, regardless of what mode we're in."""
        raise NotImplementedError("Cannot send untyped Sendable object.")   # pragma: no cover

    def send(self, context: Optional[Mapping[str, Any]]=None, priority: Optional[int]=None, mode: str=default_mode) -> None:
        """Send the message honoring the mode we're in."""
        self.setup()

        mode = mode.lower()
        self.context = context or {}

        # clean up invalid recipients
        valid_rcpts = set()
        for r in self.delivery_recipients(mode):
            try:
                if self.is_blacklisted(r):
                    if set(self.recipients) == {r}:
                        log.info("Only recipient given ('%s') is blacklisted. Giving up whole notification.", r)
                        return False
                    raise ValueError(f"Recipient address '{r}' is blacklisted.")
                valid_rcpts.add(r)
            except ValueError as err:
                log.error("n%s: Skipping invalid rcpt '%s': %s", self.nid, r, err)
        if not valid_rcpts:
            log.warning("n%s: Skipping send for lack of recipients.", self.nid)
            return False
        log.info("n%s: Sending '%s'@'%s' to: %s", self.nid, self.event(), self.vector(), valid_rcpts)
        return self.do_send(valid_rcpts, priority=priority, context=self.context)
