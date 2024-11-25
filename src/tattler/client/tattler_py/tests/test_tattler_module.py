import unittest
from unittest import mock

from urllib.error import URLError

from tattler.client import tattler_py

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