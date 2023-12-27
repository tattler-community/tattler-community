import os
import re
import logging
import socket
import getpass

from typing import Mapping, Iterable, Optional, Any
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate
import smtplib

from tattler.server.sendable.vector_sendable import Sendable, getenv

# SMTP X-Priority header
_valid_priorities = [1, 2, 3, 4, 5]
_default_priority = 3

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)

email_re = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

def get_smtp_server(connstr: str) -> [str, int]:
    """Acquire usable SMTP (host, port) pair from a connection string"""
    conn_re = '(.*)(:[0-9]+)?'
    if len(connstr.split(':')) > 2: # IPv6?
        conn_re = r'\[(.*)\](:[0-9]+)?'
    m = re.match(conn_re, connstr)
    if not m:
        raise ValueError(f"Invalid connection string {connstr}: can't detect server and (optional) port parts. Use srv:port or [srv6]:port")
    srv, port = m.groups()
    return srv, port

class EmailSendable(Sendable):
    """An e-mail message."""

    def _get_raw_content_part(self, part: str) -> [str, str]:
        filename = self._get_template_pathname() / part
        with open(filename, encoding='utf-8') as f:
            content = f.read()
        try:
            filename_base = self._get_template_pathname_base()
            filename_base = filename_base / part
            with open(filename_base, encoding='utf-8') as f:
                base_content = f.read()
            log.debug("n%s: Using template for %s -> %s", self.nid, part, filename_base)
        except Exception as err:
            log.warning("Cannot load base template: %s", err)
            base_content = None
        return content, base_content

    def _get_content_part(self, part: str, context: Mapping[str, Any]) -> str:
        # 'part' is a file contained in _get_template_pathname().
        # e.g.: foo/bar/eventname/email/subject
        content, base_content = self._get_raw_content_part(part)
        t = self.template_processor(content, base_content=base_content)
        return t.expand(context)

    def _get_parts(self) -> Iterable[str]:
        """Return the list of parts composing the template."""
        parts = []
        for part_type in ('plain', 'html'):
            partname = 'body_' + part_type
            partpath = self._get_template_pathname() / partname
            if partpath.exists():
                parts.append(part_type)
        return parts

    def raw_content(self) -> str:
        """Return raw content as either a single-part message or a multi-part MIME message"""
        # see if the message must be multi-part or plain-text
        raw_content = ''
        if not self._is_multipart():
            content, base = self._get_raw_content_part('body_plain')
            if base:
                raw_content += base
            raw_content += content
        else:
            for part_type in self._get_parts():
                content, base = self._get_raw_content_part('body_' + part_type)
                if base:
                    raw_content += base
                raw_content += content
        return raw_content

    def _auto_encode(self, content: str) -> [bytes, str]:
        """Return content encoded with the simplest possible encoding, and the ID of the encoding used."""
        # determine minimum encoding suited for this content
        for enc in 'US-ASCII', 'ISO-8859-1', 'UTF-8':
            try:
                return content.encode(enc), enc
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        # if we got here, none of the encodings worked for the content
        raise RuntimeError(f"Unable to find suitable encoding for content '{content}' among ascii, latin1 and utf8")

    def _is_multipart(self) -> bool:
        return len(self._get_parts()) > 1

    def _build_msg(self, context: Mapping[str, Any]) -> MIMEMultipart | MIMENonMultipart:
        # Create message container - the correct MIME type is multipart/alternative.
        if self._is_multipart():
            msg = MIMEMultipart('alternative')
        else:
            msg = MIMENonMultipart('text', 'plain')

        # fill out header
        msg['From'] = self.sender()
        msg['To'] = ", ".join(self.recipients)
        msg['Date'] = formatdate()
        subj, charset = self._auto_encode(self.subject(context))
        msg['Subject'] = Header(subj, charset).encode()

        # see if the message must be multi-part or plain-text
        if not self._is_multipart():
            part_content = self._get_content_part('body_plain', context)
            part_content, charset = self._auto_encode(part_content)
            msg.set_charset(charset)
            msg.set_payload(part_content)
        else:
            msg.preamble = 'Your e-mail client does not support multipart/alternative messages.'
            # Record the MIME types of both parts - text/plain and text/html.
            for part_type in self._get_parts():
                part_content = self._get_content_part('body_' + part_type, context)
                part_content, charset = self._auto_encode(part_content)
                msg.attach(MIMEText(part_content, part_type, charset))

        # add priority information, if required
        msg = self._add_priority_info(msg)

        return msg

    def validate_recipient(self, recipient: str) -> None:
        """Check that recipient is valid for current vector, and raise ValueError otherwise."""
        recipient = recipient.lower()
        regex = r'[^\s@]+@([a-z0-9_-]+\.)+([a-z0-9_-]+)'
        if re.match(regex, recipient):
            return recipient
        raise ValueError(f"Invalid recipient {recipient}: Accepted e-mail address format is '{regex}'.")

    def sender(self) -> str:
        """Return the default address to use as sender for EmailSendable"""
        sender_email = getenv("TATTLER_EMAIL_SENDER", None)
        if sender_email is None:
            log.debug("Envvar TATTLER_EMAIL_SENDER not set. Using '%s' as Email From.", sender_email)
            return f"{getpass.getuser()}@{socket.gethostname()}".lower()
        sender_email = sender_email.strip().lower()
        if not email_re.match(sender_email):
            log.error("Envvar TATTLER_EMAIL_SENDER's value '%s' is not a valid email address.", sender_email)
            raise ValueError(f"Envvar TATTLER_EMAIL_SENDER's value '{sender_email}' is not a valid email address.")
        return sender_email

    @classmethod
    def vector(cls) -> str:
        return 'email'

    def _add_priority_info(self, msg: str):
        self.priority = getattr(self, 'priority', None)
        if self.priority is None:
            # try to load it from template
            try:
                with open(os.path.join(self._get_template_pathname(), 'priority'), encoding='utf-8') as f:
                    self.set_priority(f.readline().strip())
            except IOError:
                return msg
        msg.add_header('X-Priority', str(self.priority))
        return msg

    def set_priority(self, priority: int=_default_priority) -> None:
        """Set the priority (X-Priority) of this notification.
        'priority' is in 1..5 (highest: 1), or None to disable the field."""
        if priority is None or priority is False:
            priority = _default_priority
        elif priority is True:
            priority = min(_valid_priorities)
        else:
            try:
                priority = int(priority)
            except ValueError:
                pass
        # validate value
        if priority not in _valid_priorities:
            raise ValueError(f"Invalid priority '{priority}', values are {{ None, {_valid_priorities} }}, 1 highest.")
        self.priority = priority

    def subject(self, context: Mapping[str, Any]) -> str:
        """Return the e-mail subject."""
        return self._get_content_part('subject', context).strip()

    def content(self, context: Mapping[str, Any]) -> str:
        return self._build_msg(context).as_string()

    def do_send(self, recipients: Iterable[str], priority: Optional[int]=None, context: Optional[Mapping[str, Any]]=None) -> None:
        if context is None:
            context = {}
        if priority is not None:
            self.set_priority(priority)
        msg = self.content(context)
        smtp_server, smtp_server_port = get_smtp_server(getenv("TATTLER_SMTP_ADDRESS", '127.0.0.1'))
        try:
            server = smtplib.SMTP(smtp_server, smtp_server_port)
        except ConnectionRefusedError:
            log.error("Failed to connect to SMTP server (%s:%s) to deliver email. Giving up.", smtp_server, smtp_server_port)
            raise
        smtp_tls = getenv("TATTLER_SMTP_TLS", None)
        if smtp_tls:
            server.starttls()
        smtp_auth = getenv("TATTLER_SMTP_AUTH", None)
        if smtp_auth:
            u, p = smtp_auth.split(':')
            server.login(u, p)
        server.sendmail(self.sender(), recipients, msg)
        server.quit()

