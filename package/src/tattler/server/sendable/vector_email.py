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
    def retres(srv, port):
        return srv, (int(port) if port else 25)
    connstr_ipv4_re = re.compile(r'^(?P<srv>(\d+\.){3}\d+)(:(?P<port>\d+))?$')
    mtc = connstr_ipv4_re.match(connstr)
    if mtc:
        return retres(mtc.group('srv'), mtc.group('port'))
    connstr_ipv6_re = re.compile(r'^\[(?P<srv>[a-fA-F0-9:]+)\](:(?P<port>\d+))?$')
    mtc = connstr_ipv6_re.match(connstr)
    if mtc:
        return retres(mtc.group('srv'), mtc.group('port'))
    raise ValueError(f"Invalid connection string {connstr}: can't detect server and (optional) port parts. Use srv:port or [srv6]:port")

class EmailSendable(Sendable):
    """An e-mail message."""

    def _get_available_parts(self) -> Mapping[str, str]:
        """Return the list of parts composing the template."""
        parts = self._get_template_elements()
        part_types = {
            'body_html': 'text/html',
            'body_plain': 'text/plain',
        }
        return {ptype: pname for pname, ptype in part_types.items() if pname in parts}

    def raw_content(self) -> str:
        """Return raw content as either a single-part message or a multi-part MIME message"""
        # see if the message must be multi-part or plain-text
        raw_content = ''
        for part_fname in self._get_available_parts().values():
            try:
                raw_content += self._get_template_raw_element(part_fname, base=True)
            except ValueError:
                log.debug("n%s: No base template available for element '%s'. Skipping.", self.nid, part_fname)
            raw_content += self._get_template_raw_element(part_fname)
        return raw_content

    def _auto_encode(self, content: str) -> (bytes, str):
        """Return content encoded with the simplest possible encoding, and the ID of the encoding used."""
        # determine minimum encoding suited for this content
        for enc in 'US-ASCII', 'ISO-8859-1', 'UTF-8':
            try:
                return content.encode(enc), enc
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        # if we got here, none of the encodings worked for the content
        raise RuntimeError(f"Unable to find suitable encoding for content '{content}' among ascii, latin1 and utf8")

    def _build_part_encoded(self, part_filename: str, context: Optional[Mapping[str, Any]]=None) -> (bytes, str):
        """Load content, expand it, and encode it; return content and resulting encoding.

        :param part_filename:   Filename of the part to load, e.g. 'body_plain'.
        :param context:         Optional variables to expand template with.

        :return:                Pair holding content encoded into a byte string, and name of encoding.
        """
        context = context or {}
        part_content = self._get_content_element(part_filename, context)
        return self._auto_encode(part_content)

    def _add_msg_parts(self, msg: MIMEMultipart | MIMENonMultipart, context: Optional[Mapping[str, Any]]=None) -> None:
        """Add text/html and/or text/plain parts to MIME message by loading and expanding templates and determining their encoding.
        
        :param msg:             Message to add available parts to.
        :param context:         Optional variables to expand template with.
        """
        if 'body_html' not in self._get_available_parts().values():
            part_content, charset = self._build_part_encoded('body_plain', context)
            msg.set_charset(charset)
            msg.set_payload(part_content)
        else:
            msg.preamble = 'Your e-mail client does not support multipart/alternative messages.'
            # Record the MIME types of both parts - text/plain and text/html.
            for part_type, part_fname in self._get_available_parts().items():
                part_content, charset = self._build_part_encoded(part_fname, context)
                msg.attach(MIMEText(part_content, part_type, charset))

    def _build_msg(self, context: Optional[Mapping[str, Any]]=None) -> MIMEMultipart | MIMENonMultipart:
        """Load all parts of the message and return a final email assembly.
        
        :param context:         Optional variables to expand template with.

        :return:                Email object with all required parts filled out.
        """
        # Create message container - the correct MIME type is multipart/alternative.
        if 'body_html' in self._get_available_parts().values():
            msg = MIMEMultipart('alternative')
        else:
            msg = MIMENonMultipart('text', 'plain')

        # fill out header
        msg['From'] = self.sender()
        msg['To'] = ", ".join(self.recipients)
        msg['Date'] = formatdate()
        subj, charset = self._auto_encode(self.subject(context))
        msg['Subject'] = Header(subj, charset).encode()

        self._add_msg_parts(msg, context)

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
        return self._get_content_element('subject', context).strip()

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

