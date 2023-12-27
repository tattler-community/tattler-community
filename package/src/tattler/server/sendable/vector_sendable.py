"""The abstract class parent to any message that can be delivered"""

import os
import logging
import uuid
from pathlib import Path, PurePath
from typing import Iterable, Mapping, Optional, Any

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

    def __init__(self, event: str, recipients: Iterable[str], template_processor: type(TemplateProcessor)=TemplateProcessor, template_base: str=_default_template_base, debug_recipient: Optional[str]=None):
        try:
            self.recipients = [self.validate_recipient(r) for r in recipients]
        except ValueError as err:
            raise ValueError(f"Invalid {self.vector()} recipient(s) '{recipients}': {str(err)}.") from err
        self.nid = str(uuid.uuid4())
        self.event_name = event
        self.template_base = Path(template_base)
        self.template_processor = template_processor
        self.debug_recipient_val = debug_recipient

    def _get_template_pathname_base(self) -> Path:
        template_pathname: Path = self.template_base / '_base' / self.vector()
        if not template_pathname.exists():
            raise ValueError(f"No base template exists for '{self.vector()}' (missing file: {template_pathname}).")
        return template_pathname

    def _get_template_pathname(self) -> Path:
        template_pathname = self.template_base / self.event() / self.vector()
        if not template_pathname.exists():
            raise ValueError(f"No template exists for '{self.vector()}:{self.event()}' (missing file: {template_pathname}).")
        return template_pathname

    @classmethod
    def exists(cls, event: str, template_base: str|Path) -> bool:
        """Return whether an event is available for sending over the current vector under a template base."""
        template_base = Path(template_base)
        pth = template_base / event / cls.vector()
        return pth.exists()

    def __str__(self) -> str:
        return f"{self.vector()} for '{self.event()}' to '{self.recipients}'"

    def blacklist(self, filename: Optional[str|Path]=None) -> None:
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

    def validate_recipient(self, recipient: str) -> str:
        """Return normalized recipient, or raise ValueError if invalid."""
        return recipient

    def event(self) -> str:
        """Return the event name for the current sendable"""
        return self.event_name

    @classmethod
    def vector(cls) -> str:
        """Return the vector name for a given sendable class."""
        return 'Sendable'

    def raw_content(self) -> str:
        """Return the raw content of the unexpanded template."""
        tmplp = self._get_template_pathname()
        return tmplp.read_text(encoding='utf-8')

    def content(self, context: Mapping[str, Any]) -> str:
        """Return the content of the sendable."""
        template_path = self._get_template_pathname()
        templbody = template_path.read_text(encoding='utf-8')
        templ: TemplateProcessor = self.template_processor(templbody)
        return templ.expand(context)
    
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

    def do_send(self, recipients: Iterable[str], priority: Optional[int]=None, context: Optional[Mapping[str, Any]]=None) -> None:
        """Concretely send the message, regardless of what mode we're in."""
        raise NotImplementedError("Cannot send untyped Sendable object.")

    def send(self, context: Optional[Mapping[str, Any]]=None, priority: Optional[int]=None, mode: str=default_mode) -> None:
        """Send the message honoring the mode we're in."""
        mode = mode.lower()
        context = context or {}
        self.context = context

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
        return self.do_send(valid_rcpts, priority=priority, context=context)
