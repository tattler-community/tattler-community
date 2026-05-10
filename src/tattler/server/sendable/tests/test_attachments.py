"""Tests for attachment normalization, URL fetcher, and MIME assembly."""

import base64
import email
import http.server
import socket
import threading
import time
import unittest
from pathlib import Path

from tattler.server.sendable import attachments
from tattler.server.sendable.attachments import (
    Attachment, normalize_attachments, _sniff_image,
)
from tattler.server.sendable.vector_email import EmailSendable


tbase_attachments = Path(__file__).parent / 'fixtures' / 'templates'
PNG_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
    b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
)
PNG_B64 = base64.b64encode(PNG_BYTES).decode()
PDF_BYTES = b'%PDF-1.4\n%fake pdf body\n'


class _CannedHandler(http.server.BaseHTTPRequestHandler):
    """Per-server: response and side-effects come from server attributes."""

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        srv = self.server
        srv.paths_seen.append(self.path)
        if getattr(srv, 'sleep_before', 0):
            time.sleep(srv.sleep_before)
        if srv.mode == 'ok':
            self.send_response(200)
            for k, v in (srv.headers_extra or {}).items():
                self.send_header(k, v)
            self.send_header('Content-Length', str(len(srv.body)))
            self.end_headers()
            self.wfile.write(srv.body)
        elif srv.mode == 'redirect':
            self.send_response(302)
            self.send_header('Location', srv.redirect_to)
            self.end_headers()
        elif srv.mode == 'redirect_loop':
            srv.hop_count += 1
            self.send_response(302)
            # always redirect back to self
            self.send_header('Location', f'http://{srv.server_address[0]}:{srv.server_address[1]}/loop')
            self.end_headers()
        elif srv.mode == '500':
            self.send_response(500)
            self.end_headers()


def _start_server(**attrs):
    srv = http.server.HTTPServer(('127.0.0.1', 0), _CannedHandler)
    for k, v in attrs.items():
        setattr(srv, k, v)
    srv.headers_extra = attrs.get('headers_extra')
    srv.body = attrs.get('body', b'')
    srv.sleep_before = attrs.get('sleep_before', 0)
    srv.hop_count = 0
    srv.paths_seen = []
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, t


class TestSniffImage(unittest.TestCase):

    def test_png(self):
        self.assertEqual(_sniff_image(PNG_BYTES), ('image', 'png', '.png'))

    def test_jpeg(self):
        self.assertEqual(_sniff_image(b'\xff\xd8\xff\xe0fake'), ('image', 'jpeg', '.jpg'))

    def test_gif(self):
        self.assertEqual(_sniff_image(b'GIF89a fake'), ('image', 'gif', '.gif'))
        self.assertEqual(_sniff_image(b'GIF87a fake'), ('image', 'gif', '.gif'))

    def test_webp(self):
        self.assertEqual(_sniff_image(b'RIFF\x00\x00\x00\x00WEBPfake'),
                         ('image', 'webp', '.webp'))

    def test_svg_xml_decl(self):
        self.assertEqual(_sniff_image(b'<?xml version="1.0"?><svg></svg>'),
                         ('image', 'svg+xml', '.svg'))

    def test_svg_bare(self):
        self.assertEqual(_sniff_image(b'  <svg xmlns="..."></svg>'),
                         ('image', 'svg+xml', '.svg'))

    def test_unknown_returns_none(self):
        self.assertIsNone(_sniff_image(b'\x00\x00not an image'))
        self.assertIsNone(_sniff_image(PDF_BYTES))
        self.assertIsNone(_sniff_image(b''))


class TestNormalizeAttachments(unittest.TestCase):

    def test_empty_returns_empty_list(self):
        self.assertEqual(normalize_attachments(None), [])
        self.assertEqual(normalize_attachments({}), [])

    def test_must_be_dict(self):
        with self.assertRaisesRegex(ValueError, "must be a dict"):
            normalize_attachments([{'filename': 'a.png', 'content_b64': PNG_B64}])

    # regular attachments

    def test_regular_b64(self):
        out = normalize_attachments({'a.png': {'content_b64': PNG_B64}})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].filename, 'a.png')
        self.assertEqual(out[0].content, PNG_BYTES)
        self.assertEqual((out[0].maintype, out[0].subtype), ('image', 'png'))
        self.assertIsNone(out[0].cid)

    def test_regular_content_bytes(self):
        out = normalize_attachments({'a.png': {'content_bytes': PNG_BYTES}})
        self.assertEqual(out[0].content, PNG_BYTES)

    def test_regular_unknown_extension_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot determine content type"):
            normalize_attachments({'a.weirdext': {'content_b64': PNG_B64}})

    def test_regular_no_extension_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot determine content type"):
            normalize_attachments({'noext': {'content_b64': PNG_B64}})

    def test_regular_invalid_filename_with_slash_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid filename"):
            normalize_attachments({'../etc/passwd': {'content_bytes': PNG_BYTES}})

    def test_regular_filename_starting_with_dot_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid filename"):
            normalize_attachments({'.hidden.png': {'content_bytes': PNG_BYTES}})

    # inline attachments (key contains '@')

    def test_inline_b64_sniffs_type(self):
        out = normalize_attachments({'logo@local': {'content_b64': PNG_B64}})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].cid, 'logo@local')
        self.assertEqual((out[0].maintype, out[0].subtype), ('image', 'png'))
        # filename is synthesized from cid local-part + sniffed extension
        self.assertEqual(out[0].filename, 'logo.png')

    def test_inline_content_bytes_sniffs_type(self):
        out = normalize_attachments({'pic@x': {'content_bytes': PNG_BYTES}})
        self.assertEqual(out[0].cid, 'pic@x')
        self.assertEqual((out[0].maintype, out[0].subtype), ('image', 'png'))
        self.assertEqual(out[0].filename, 'pic.png')

    def test_inline_unsupported_format_rejected(self):
        with self.assertRaisesRegex(ValueError, "could not detect image type"):
            normalize_attachments({'doc@x': {'content_bytes': PDF_BYTES}})

    def test_inline_cid_with_whitespace_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid characters"):
            normalize_attachments({'has space@x': {'content_b64': PNG_B64}})

    def test_inline_cid_with_angle_brackets_rejected(self):
        for bad in ['<logo@x', 'log>@x', 'a<b@x']:
            with self.assertRaisesRegex(ValueError, "invalid characters"):
                normalize_attachments({bad: {'content_b64': PNG_B64}})

    def test_inline_dict_dedups_cid_structurally(self):
        # Python dict literals with duplicate keys keep the last; same applies to JSON.
        # The structure itself enforces uniqueness, so there's nothing for the
        # validator to reject -- just sanity-check that it parses.
        out = normalize_attachments({'logo@x': {'content_b64': PNG_B64}})
        self.assertEqual(len(out), 1)

    # source-of-content validation

    def test_no_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly one of"):
            normalize_attachments({'a.png': {}})

    def test_multiple_sources_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly one of"):
            normalize_attachments({'a.png': {'content_b64': PNG_B64,
                                              'content_bytes': PNG_BYTES}})

    def test_malformed_base64_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid base64"):
            normalize_attachments({'a.png': {'content_b64': '@@@not base64@@@'}})

    def test_content_bytes_must_be_bytes(self):
        with self.assertRaisesRegex(ValueError, "must be bytes"):
            normalize_attachments({'a.png': {'content_bytes': 'not-bytes'}})

    def test_entry_must_be_object(self):
        with self.assertRaisesRegex(ValueError, "must be an object"):
            normalize_attachments({'a.png': 'not a dict'})

    def test_empty_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-empty string"):
            normalize_attachments({'': {'content_b64': PNG_B64}})

    # size cap

    def test_total_size_cap_enforced(self):
        big = b'\x00' * (attachments.TOTAL_MAX_BYTES + 1)
        with self.assertRaisesRegex(ValueError, "exceed total cap"):
            normalize_attachments({'big.bin': {'content_bytes': big}})


class TestUrlFetcher(unittest.TestCase):

    def _url(self, srv, path='/file.png'):
        host, port = srv.server_address
        return f'http://{host}:{port}{path}'

    def test_regular_url_keyed_by_filename(self):
        srv, _ = _start_server(mode='ok', body=PNG_BYTES)
        try:
            out = normalize_attachments({'foo.png': {'url': self._url(srv, '/ignored')}})
            self.assertEqual(out[0].filename, 'foo.png')
            self.assertEqual(out[0].content, PNG_BYTES)
        finally:
            srv.shutdown()

    def test_inline_url_sniffs_type(self):
        srv, _ = _start_server(mode='ok', body=PNG_BYTES)
        try:
            out = normalize_attachments({'logo@x': {'url': self._url(srv, '/ignored')}})
            self.assertEqual(out[0].cid, 'logo@x')
            self.assertEqual(out[0].filename, 'logo.png')
            self.assertEqual((out[0].maintype, out[0].subtype), ('image', 'png'))
        finally:
            srv.shutdown()

    def test_url_query_string_passed_through(self):
        srv, _ = _start_server(mode='ok', body=PNG_BYTES)
        try:
            normalize_attachments({'foo.png': {
                'url': self._url(srv, '/path?token=abc&v=1'),
            }})
            self.assertEqual(srv.paths_seen, ['/path?token=abc&v=1'])
        finally:
            srv.shutdown()

    def test_redirect_followed(self):
        target, _ = _start_server(mode='ok', body=PNG_BYTES)
        host, port = target.server_address
        src, _ = _start_server(mode='redirect', redirect_to=f'http://{host}:{port}/foo.png')
        try:
            out = normalize_attachments({'foo.png': {'url': self._url(src, '/start')}})
            self.assertEqual(out[0].content, PNG_BYTES)
        finally:
            src.shutdown()
            target.shutdown()

    def test_redirect_loop_hits_cap(self):
        srv, _ = _start_server(mode='redirect_loop')
        try:
            with self.assertRaisesRegex(ValueError, "Too many redirects"):
                normalize_attachments({'x.png': {'url': self._url(srv, '/loop')}})
        finally:
            srv.shutdown()

    def test_body_exceeds_cap(self):
        big = b'\x00' * (attachments.TOTAL_MAX_BYTES + 1024)
        srv, _ = _start_server(mode='ok', body=big)
        try:
            with self.assertRaisesRegex(ValueError, "exceeded"):
                normalize_attachments({'big.bin': {'url': self._url(srv, '/big')}})
        finally:
            srv.shutdown()

    def test_bad_scheme_rejected(self):
        with self.assertRaisesRegex(ValueError, "scheme"):
            normalize_attachments({'a.png': {'url': 'file:///etc/passwd'}})

    def test_http_500_rejected(self):
        srv, _ = _start_server(mode='500')
        try:
            with self.assertRaisesRegex(ValueError, "HTTP 500"):
                normalize_attachments({'x.png': {'url': self._url(srv, '/x')}})
        finally:
            srv.shutdown()

    def test_slow_server_trips_read_timeout(self):
        original = attachments.READ_TIMEOUT_S
        attachments.READ_TIMEOUT_S = 1
        srv, _ = _start_server(mode='ok', body=PNG_BYTES, sleep_before=2)
        try:
            with self.assertRaises((socket.timeout, TimeoutError, OSError)):
                normalize_attachments({'slow.png': {'url': self._url(srv, '/slow')}})
        finally:
            attachments.READ_TIMEOUT_S = original
            srv.shutdown()


class TestEmailMimeStructure(unittest.TestCase):
    """Walk the assembled message and check the structure matches the design."""

    def _msg(self, atts):
        e = EmailSendable(
            'event_with_attachments',
            ['someone@example.com'],
            template_base=tbase_attachments,
        )
        ctx = {'one': 'X', '_attachments': atts}
        raw = e.content(context=ctx)
        return email.message_from_string(raw)

    def test_no_attachments_remains_alternative(self):
        e = EmailSendable(
            'event_with_attachments',
            ['someone@example.com'],
            template_base=tbase_attachments,
        )
        msg = email.message_from_string(e.content(context={'one': 'X'}))
        self.assertEqual(msg.get_content_type(), 'multipart/alternative')

    def test_inline_only_nests_related_in_alternative(self):
        msg = self._msg({'logo@local': {'content_b64': PNG_B64}})
        self.assertEqual(msg.get_content_type(), 'multipart/alternative')
        alt_children = msg.get_payload()
        self.assertEqual(alt_children[0].get_content_type(), 'text/plain')
        related = alt_children[1]
        self.assertEqual(related.get_content_type(), 'multipart/related')
        related_children = related.get_payload()
        self.assertEqual(related_children[0].get_content_type(), 'text/html')
        self.assertEqual(related_children[1]['Content-ID'], '<logo@local>')
        self.assertIn('inline', related_children[1].get('Content-Disposition', ''))

    def test_regular_only_wraps_in_mixed(self):
        msg = self._msg({'doc.pdf': {'content_bytes': PDF_BYTES}})
        self.assertEqual(msg.get_content_type(), 'multipart/mixed')
        children = msg.get_payload()
        self.assertEqual(children[0].get_content_type(), 'multipart/alternative')
        self.assertIn('attachment', children[1].get('Content-Disposition', ''))

    def test_mixed_inline_and_regular(self):
        msg = self._msg({
            'logo@local': {'content_b64': PNG_B64},
            'invoice.pdf': {'content_bytes': PDF_BYTES},
        })
        self.assertEqual(msg.get_content_type(), 'multipart/mixed')
        children = msg.get_payload()
        alt = children[0]
        self.assertEqual(alt.get_content_type(), 'multipart/alternative')
        alt_children = alt.get_payload()
        self.assertEqual(alt_children[0].get_content_type(), 'text/plain')
        related = alt_children[1]
        self.assertEqual(related.get_content_type(), 'multipart/related')
        related_children = related.get_payload()
        self.assertEqual(related_children[0].get_content_type(), 'text/html')
        self.assertEqual(related_children[1]['Content-ID'], '<logo@local>')
        self.assertIn('attachment', children[1].get('Content-Disposition', ''))

    def test_inline_without_html_demotes_to_regular(self):
        # Plain-only template (no body.html). An inline-keyed attachment can't
        # be referenced from HTML, so it falls back to a regular attachment.
        e = EmailSendable(
            'event_with_email_plain',
            ['someone@example.com'],
            template_base=tbase_attachments,
        )
        ctx = {'_attachments': {'logo@local': {'content_b64': PNG_B64}}}
        msg = email.message_from_string(e.content(context=ctx))
        # Outer is multipart/mixed (text body + the demoted attachment).
        self.assertEqual(msg.get_content_type(), 'multipart/mixed')
        children = msg.get_payload()
        self.assertEqual(children[0].get_content_type(), 'text/plain')
        # The demoted entry shows up as an attachment, not inline; no Content-ID.
        att_part = children[1]
        self.assertIn('attachment', att_part.get('Content-Disposition', ''))
        self.assertIsNone(att_part.get('Content-ID'))

    def test_orphan_cid_ref_does_not_break_build(self):
        # Template references cid:logo@local but no attachment supplies it.
        e = EmailSendable(
            'event_with_attachments',
            ['someone@example.com'],
            template_base=tbase_attachments,
        )
        raw = e.content(context={'one': 'X'})
        msg = email.message_from_string(raw)
        self.assertEqual(msg.get_content_type(), 'multipart/alternative')
        for part in msg.walk():
            self.assertNotEqual(part.get('Content-ID'), '<logo@local>')

    def test_attachments_key_consumed_not_rendered(self):
        e = EmailSendable(
            'event_with_attachments',
            ['someone@example.com'],
            template_base=tbase_attachments,
        )
        raw = e.content(context={
            'one': 'X',
            '_attachments': {'a.txt': {'content_bytes': b'hi there'}},
        })
        # The literal context-key name should not leak into the rendered output.
        self.assertNotIn("'_attachments'", raw)
