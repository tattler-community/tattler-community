"""Attachment normalization and URL fetching for EmailSendable.

Caller and plugin attachments share one shape: a dict whose keys disambiguate
inline images from regular file attachments by format alone.

    {
      "_attachments": {
        "logo@local":   {"content_b64": "..."},
        "invoice.pdf":  {"url": "https://internal.example.com/invoice.pdf"}
      }
    }

A key containing ``@`` is the Content-ID of an inline image (referenced from
HTML as ``cid:<key>``); content type is auto-detected from the bytes. A key
without ``@`` is the filename of a regular attachment, and the key drives
content type via :func:`mimetypes.guess_type`.

Plugins use the same shape with ``content_bytes`` (raw ``bytes``) instead of
``content_b64``.
"""

import base64
import binascii
import http.client
import logging
import mimetypes
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple
from urllib.parse import urljoin, urlparse

log = logging.getLogger(__name__)

# Defaults chosen for SMTP relays with ~10 MB caps; ~7 MB raw -> ~9.5 MB after base64.
TOTAL_MAX_BYTES = 7 * 1024 * 1024
CONNECT_TIMEOUT_S = 3
READ_TIMEOUT_S = 20
MAX_REDIRECTS = 5
CHUNK_SIZE = 64 * 1024


@dataclass
class Attachment:
    """Normalized attachment ready for MIME assembly."""
    filename: str
    content: bytes
    maintype: str
    subtype: str
    cid: Optional[str] = None


def _fetch_url(url: str, max_bytes: int) -> bytes:
    """Fetch an HTTP(S) URL and return the response body as bytes.

    Streams the response with a per-chunk read timeout and aborts as soon as
    the running total exceeds max_bytes. Follows up to MAX_REDIRECTS hops.
    """
    visited = 0
    current = url
    while True:
        if visited > MAX_REDIRECTS:
            raise ValueError(f"Too many redirects fetching {url}")

        parsed = urlparse(current)
        if parsed.scheme not in ('http', 'https'):
            raise ValueError(f"URL scheme '{parsed.scheme}' not supported; use http or https.")
        if not parsed.hostname:
            raise ValueError(f"URL missing host: {current}")

        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        path = parsed.path or '/'
        if parsed.query:
            path = f"{path}?{parsed.query}"

        ConnCls = http.client.HTTPSConnection if parsed.scheme == 'https' else http.client.HTTPConnection
        conn = ConnCls(parsed.hostname, port, timeout=CONNECT_TIMEOUT_S)

        try:
            conn.connect()
            # swap to per-recv read timeout; a steady stream never trips, a stalled one does
            conn.sock.settimeout(READ_TIMEOUT_S)
            conn.request("GET", path, headers={"Host": parsed.netloc, "User-Agent": "tattler"})
            resp = conn.getresponse()

            if 300 <= resp.status < 400 and resp.getheader("Location"):
                visited += 1
                current = urljoin(current, resp.getheader("Location"))
                resp.read()  # drain so the connection can close cleanly
                continue

            if resp.status != 200:
                raise ValueError(f"Fetch of {url} returned HTTP {resp.status}")

            buf = bytearray()
            while True:
                chunk = resp.read(CHUNK_SIZE)
                if not chunk:
                    break
                buf.extend(chunk)
                if len(buf) > max_bytes:
                    raise ValueError(f"Attachment from {url} exceeded {max_bytes} bytes")
            return bytes(buf)
        finally:
            conn.close()


def _validate_filename(filename, label: str) -> None:
    """Raise ValueError if ``filename`` is not an acceptable basename."""
    if (not isinstance(filename, str) or not filename
            or '/' in filename or '\\' in filename or filename.startswith('.')):
        raise ValueError(f"{label}: invalid filename '{filename}'")


def _validate_cid(cid: str, label: str) -> None:
    """Raise ValueError if ``cid`` is not an acceptable Content-ID token."""
    if (not cid.isprintable()
            or any(c.isspace() for c in cid)
            or '<' in cid or '>' in cid):
        raise ValueError(f"{label}: 'cid' contains invalid characters")


def _sniff_image(data: bytes) -> Optional[Tuple[str, str, str]]:
    """Return ``(maintype, subtype, extension)`` for an inline image, or ``None``.

    Recognizes the formats commonly used for inline HTML email images:
    PNG, JPEG, GIF, WebP, and SVG. We deliberately don't depend on libmagic
    (native dep) or ``imghdr`` (removed in Python 3.13).
    """
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image', 'png', '.png'
    if data.startswith(b'\xff\xd8\xff'):
        return 'image', 'jpeg', '.jpg'
    if data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
        return 'image', 'gif', '.gif'
    if len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image', 'webp', '.webp'
    head = data[:512].lstrip().lower()
    if head.startswith(b'<?xml') or head.startswith(b'<svg'):
        return 'image', 'svg+xml', '.svg'
    return None


def normalize_attachments(raw: Optional[Mapping]) -> list:
    """Validate, fetch, and normalize an attachment dict.

    Each (key, entry) pair becomes one Attachment:

    * key contains ``@`` -> inline image: key IS the Content-ID, entry must
      supply ``filename`` (drives content type).
    * key has no ``@``  -> regular attachment: key IS the filename and drives
      content type.

    The entry must specify exactly one of ``url``, ``content_b64``, or
    ``content_bytes`` for the payload. Raises ValueError on any invalid entry.
    """
    if not raw:
        return []

    if not isinstance(raw, Mapping):
        raise ValueError("Attachments must be a dict")

    out = []
    total = 0

    for key, entry in raw.items():
        label = f"Attachment '{key}'"
        if not isinstance(key, str) or not key:
            raise ValueError(f"{label}: key must be a non-empty string")
        if not isinstance(entry, Mapping):
            raise ValueError(f"{label}: must be an object")

        is_inline = '@' in key
        if is_inline:
            cid = key
            _validate_cid(cid, label)
        else:
            cid = None
            _validate_filename(key, label)

        sources = [k for k in ('url', 'content_b64', 'content_bytes') if k in entry]
        if len(sources) != 1:
            raise ValueError(
                f"{label}: must specify exactly one of 'url', 'content_b64', 'content_bytes'")
        source = sources[0]

        if source == 'url':
            remaining = TOTAL_MAX_BYTES - total
            if remaining <= 0:
                raise ValueError(f"Attachments exceed total cap of {TOTAL_MAX_BYTES} bytes")
            content = _fetch_url(entry['url'], remaining)
        elif source == 'content_b64':
            try:
                content = base64.b64decode(entry['content_b64'], validate=True)
            except (ValueError, binascii.Error) as err:
                raise ValueError(f"{label}: invalid base64: {err}") from err
        else:  # content_bytes
            content = entry['content_bytes']
            if not isinstance(content, (bytes, bytearray)):
                raise ValueError(f"{label}: 'content_bytes' must be bytes")
            content = bytes(content)

        if is_inline:
            sniffed = _sniff_image(content)
            if sniffed is None:
                raise ValueError(
                    f"{label}: could not detect image type from content; "
                    "supported inline formats are PNG, JPEG, GIF, WebP, SVG")
            maintype, subtype, ext = sniffed
            filename = f"{cid.split('@', 1)[0]}{ext}"
        else:
            filename = key
            guessed, _ = mimetypes.guess_type(filename)
            if not guessed:
                raise ValueError(
                    f"{label}: cannot determine content type for '{filename}'; "
                    "rename with a recognized extension")
            maintype, subtype = guessed.split('/', 1)

        total += len(content)
        if total > TOTAL_MAX_BYTES:
            raise ValueError(f"Attachments exceed total cap of {TOTAL_MAX_BYTES} bytes")

        out.append(Attachment(filename=filename, content=content,
                              maintype=maintype, subtype=subtype, cid=cid))
        log.info("Accepted attachment %s (%d bytes, %s/%s%s)",
                 filename, len(content), maintype, subtype,
                 f", cid={cid}" if cid else "")

    return out
