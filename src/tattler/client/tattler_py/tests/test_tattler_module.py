import base64
import os
import unittest
from pathlib import Path
from unittest import mock

from urllib.error import URLError

from tattler.client import tattler_py
from tattler.client.tattler_py import translate_attachments

class TattlerModuleTest(unittest.TestCase):
    """Test cases for the tattler.client module"""

    def test_mk_correlation_id(self):
        """mk_correlation_id() produces a minimum length and entropy"""
        for i in range(100):
            cid = tattler_py.mk_correlation_id(None)
            self.assertIsInstance(cid, str, msg=f"{i}th call to mk_correlation_id() returned non-string")
            self.assertGreaterEqual(len(cid), 10, msg=f"{i}th call to mk_correlation_id() returned ID shorter than 10 = '{cid}'")
            self.assertGreaterEqual(len(set(cid)), 6, msg=f"{i}th call to mk_correlation_id() returned insufficient entropy {len(set(cid))} for '{cid}'")
    
    def test_mk_correlation_id_with_prefix(self):
        """mk_correlation_id() produces IDs prefixed by requested or default prefix"""
        cid = tattler_py.mk_correlation_id('x')
        self.assertIsInstance(cid, str)
        self.assertTrue(cid.startswith('x:'))

    def test_send_notification_prioritizes_cmdline(self):
        """send_notification() never looks up server address configuration if either srv_addr or srv_port are set"""
        with mock.patch('tattler.client.tattler_py.TattlerClientHTTP'):
            with mock.patch('tattler.client.tattler_py.tattler_client_utils.getenv') as mgetenv:
                mgetenv.side_effect = lambda k,v=None: {'TATTLER_SERVER_ADDRESS': None}.get(k, os.getenv(k, v))
                tattler_py.send_notification('scope', 'event', 'rcpt', srv_addr='1.2.3.4', srv_port=1234)
                mgetenv.assert_not_called()
                mgetenv.reset_mock()
                tattler_py.send_notification('scope', 'event', 'rcpt', srv_addr='1.2.3.4')
                mgetenv.assert_not_called()
                mgetenv.reset_mock()
                tattler_py.send_notification('scope', 'event', 'rcpt', srv_port=1234)
                mgetenv.assert_not_called()
                mgetenv.reset_mock()

    def test_send_notification_searches_endpoint_envvar_config(self):
        """send_notification() looks up server address configuration in right envvar"""
        with mock.patch('tattler.client.tattler_py.TattlerClientHTTP') as mnotif:
            with mock.patch('tattler.client.tattler_py.tattler_client_utils.getenv') as mgetenv:
                mgetenv.side_effect = lambda k,v=None: {'TATTLER_SERVER_ADDRESS': '12.13.14.15:100'}.get(k, os.getenv(k, v))
                tattler_py.send_notification('scope', 'event', 'rcpt')
                mgetenv.assert_called_with('TATTLER_SERVER_ADDRESS')
                self.assertEqual(1, mnotif.call_count)
                self.assertEqual('12.13.14.15', mnotif.call_args.args[1])
                self.assertEqual(100, mnotif.call_args.args[2])

    def test_send_notification_fails_silently(self):
        """send_notification() reports errors in retval instead of raising"""
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.side_effect = URLError("Artificial test error")
            success, detail = tattler_py.send_notification('scope', 'event', 'rcpt')
            self.assertFalse(success)
            self.assertIsInstance(detail, dict)
            self.assertIn('error', detail)
    
    def test_send_notification_sends(self):
        """send_notification() calls send() on the notification client object"""
        with mock.patch('tattler.client.tattler_py.TattlerClientHTTP') as mnotif:
            ctx = {'a': 1, 'b': 'foo', 'c': None }
            cid = '1234'
            tattler_py.send_notification('scope', 'event', 'rcpt', context=ctx, correlationId=cid)
            mnotif.assert_called()
            mnotif.return_value.send.assert_called()
            wanted_vars = {
                'vectors': None,
                'event': 'event',
                'recipient': 'rcpt',
                'context': ctx,
                'correlationId': cid
            }
            for wanted_name, wanted_val in wanted_vars.items():
                self.assertIn(wanted_name, mnotif.return_value.send.call_args.kwargs)
                self.assertEqual(mnotif.return_value.send.call_args.kwargs[wanted_name], wanted_val)

    def test_send_notification_reports_failure(self):
        """If underlying send() fails, client returns False"""
        with mock.patch('tattler.client.tattler_py.TattlerClientHTTP') as mtatcli:
            mtatcli.return_value.send.side_effect = RuntimeError("Foobar")
            res = tattler_py.send_notification('scope', 'event', 'rcpt')
            self.assertIsInstance(res, tuple)
            self.assertEqual(2, len(res))
            self.assertEqual(False, res[0])
            self.assertIsInstance(res[1], dict)

    def testtranslate_attachments_path_reads_and_b64s(self):
        """A Path value is read and base64-encoded into wire format"""
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'hello bytes')
            tmp = Path(f.name)
        try:
            out = translate_attachments({'a.bin': tmp})
            self.assertEqual(out, {'a.bin': {
                'content_b64': base64.b64encode(b'hello bytes').decode()}})
        finally:
            tmp.unlink()

    def testtranslate_attachments_url_str_forwarded(self):
        """An http(s):// string value is forwarded as a URL entry"""
        for url in ('http://x/a', 'https://y/b'):
            self.assertEqual(translate_attachments({'a.png': url}),
                             {'a.png': {'url': url}})

    def testtranslate_attachments_str_without_scheme_rejected(self):
        with self.assertRaisesRegex(ValueError, "http\\(s\\)://"):
            translate_attachments({'a.png': 'just-a-string'})

    def testtranslate_attachments_unsupported_scheme_rejected(self):
        for bad in ('file:///etc/passwd', 'ftp://x', 'data:text/plain,hi'):
            with self.assertRaisesRegex(ValueError, "http\\(s\\)://"):
                translate_attachments({'a.png': bad})

    def testtranslate_attachments_wrong_type_rejected(self):
        for bad in (b'raw bytes', {'url': 'http://x'}, 42, None):
            with self.assertRaises(TypeError):
                translate_attachments({'a.png': bad})

    def test_send_notification_attachments_param_injects_into_context(self):
        """attachments= is translated into context['_attachments'] before sending"""
        with mock.patch('tattler.client.tattler_py.TattlerClientHTTP') as mnotif:
            tattler_py.send_notification(
                'scope', 'event', 'rcpt',
                context={'name': 'Alice'},
                attachments={'logo@brand': 'https://x/logo.png'})
            ctx_sent = mnotif.return_value.send.call_args.kwargs['context']
            self.assertEqual(ctx_sent['name'], 'Alice')
            self.assertEqual(ctx_sent['_attachments'],
                             {'logo@brand': {'url': 'https://x/logo.png'}})

    def test_send_notification_rejects_double_attachments(self):
        """Passing attachments= and context['_attachments'] together raises (programmer error)"""
        with mock.patch('tattler.client.tattler_py.TattlerClientHTTP'):
            with self.assertRaisesRegex(ValueError, "not both"):
                tattler_py.send_notification(
                    'scope', 'event', 'rcpt',
                    context={'_attachments': {}},
                    attachments={'a.png': 'https://x/a.png'})

    def test_send_notification_no_attachments_leaves_context_alone(self):
        """When attachments= is not passed, context is not mutated to add _attachments"""
        with mock.patch('tattler.client.tattler_py.TattlerClientHTTP') as mnotif:
            tattler_py.send_notification('scope', 'event', 'rcpt', context={'a': 1})
            ctx_sent = mnotif.return_value.send.call_args.kwargs['context']
            self.assertNotIn('_attachments', ctx_sent)

    def test_module_exports_expected_symbols(self):
        """The client module exports all symbols intended public"""
        with mock.patch('tattler.client.tattler_py.mk_correlation_id'):
            pass
        with mock.patch('tattler.client.tattler_py.send_notification'):
            pass
        with mock.patch('tattler.client.tattler_py.TattlerClient'):
            pass
        with mock.patch('tattler.client.tattler_py.TattlerClientHTTP'):
            pass


if __name__ == '__main__':
    unittest.main()
