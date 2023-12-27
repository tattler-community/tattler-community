import unittest
from unittest import mock

import os
from urllib.error import URLError

os.environ['TATTLER_SERVER'] = '127.0.0.1:123'

from tattler.client import tattler_py

class TattlerModuleTest(unittest.TestCase):
    def test_mk_correlation_id(self):
        self.assertIsInstance(tattler_py.mk_correlation_id(), str)
    
    def test_send_notification_fails_silently(self):
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.side_effect = URLError("Artificial test error")
            tattler_py.send_notification('scope', 'event', 'rcpt')
    
    def test_send_notification_sends(self):
        with mock.patch('tattler.client.tattler_py.TattlerClientHTTP') as mnotif:
            ctx = {'a': 1, 'b': 'foo', 'c': None }
            cid = '1234'
            tattler_py.send_notification('scope', 'event', 'rcpt', context=ctx, correlationId=cid)
            mnotif.assert_called()
            mnotif().send.assert_called()
            wanted_vars = {
                'vectors': None,
                'event': 'event',
                'recipient': 'rcpt',
                'context': ctx,
                'correlationId': cid
            }
            for wanted_name, wanted_val in wanted_vars.items():
                self.assertIn(wanted_name, mnotif().send.call_args.kwargs)
                self.assertEqual(mnotif().send.call_args.kwargs[wanted_name], wanted_val)
