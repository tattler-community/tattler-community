import unittest
from unittest import mock
import urllib

from tattler.server.sendable.bulksms import BulkSMS


class TestBulkSMS(unittest.TestCase):
    def test_construction_succeeds(self):
        b = BulkSMS('foo:')
        self.assertIsNotNone(b)
        b = BulkSMS('foo:', sender='+123')
        self.assertIsNotNone(b)
        b = BulkSMS('foo:', sender='00123')
        self.assertIsNotNone(b)
        b = BulkSMS('foo:', sender='sender_name123')
        self.assertIsNotNone(b)

    def test_construction_missing_data_rejected(self):
        with self.assertRaises(ValueError):
            b = BulkSMS()
    
    def test_get_recipient_normalize(self):
        s = BulkSMS('foo')
        self.assertIsNone(s.get_sender())
        self.assertEqual(s.get_sender('00123'), '+123')

    def test_send_single_recipient(self):
        s = BulkSMS('foo')
        with mock.patch('tattler.server.sendable.bulksms.urllib.request') as mreq:
            # with urlopen() as f: f.read()
            mreq.urlopen().__enter__().read.return_value = b"{}"
            s.send('123', 'Content')
            self.assertTrue(mreq.Request.mock_calls)

    def test_send_sender_and_recipients_in_call(self):
        s = BulkSMS('foo')
        with mock.patch('tattler.server.sendable.bulksms.urllib.request') as mreq:
            # with urlopen() as f: f.read()
            mreq.urlopen().__enter__().read.return_value = b"{}"
            s.send(['rcpt123', 'rcpt456'], 'Content', sender='sndr321')
            self.assertTrue(mreq.Request.mock_calls)
            self.assertIn('data', mreq.Request.call_args.kwargs)
            self.assertIsInstance(mreq.Request.call_args.kwargs['data'], bytes)
            self.assertIn(b'rcpt123', mreq.Request.call_args.kwargs['data'])
            self.assertIn(b'rcpt456', mreq.Request.call_args.kwargs['data'])
            self.assertIn(b'sndr321', mreq.Request.call_args.kwargs['data'])

    def test_send_backend_error_raised(self):
        s = BulkSMS('foo')
        with mock.patch('tattler.server.sendable.bulksms.urllib.request') as mreq:
            # with urlopen() as f: f.read()
            mreq.urlopen().__enter__().read.side_effect = urllib.error.URLError("Connection refused")
            with self.assertRaises(Exception):
                s.send(['123'], 'Content')
    
    def test_delivery_status_requests_correct_msg(self):
        s = BulkSMS('foo')
        with mock.patch('tattler.server.sendable.bulksms.urllib.request') as mreq:
            mreq.urlopen().__enter__().read.return_value = b"""[ {"status": { "type": "delivered" }} ]"""
            s.msg_delivery_status('msg1234xyz')
            self.assertTrue(mreq.Request.call_args.args)
            self.assertIn('msg1234xyz', mreq.Request.call_args.args[0])

    def test_delivery_status_requests_error_raised(self):
        s = BulkSMS('foo')
        with mock.patch('tattler.server.sendable.bulksms.urllib.request') as mreq:
            # invalid response
            err = urllib.error.URLError("Connection refused")
            mreq.urlopen().__enter__().read.side_effect = err
            with self.assertRaises(type(err)):
                s.msg_delivery_status('msg1234xyz')
            # valid response, invalid JSON
            mreq.urlopen().__enter__().read.return_value = b"""invalid [ json junk }"""
            mreq.urlopen().__enter__().read.side_effect = None
            with self.assertRaises(ValueError):
                s.msg_delivery_status('msg1234xyz')
            # valid response, valid JSON, missing fields
            mreq.urlopen().__enter__().read.return_value = b"""[]"""
            mreq.urlopen().__enter__().read.side_effect = None
            with self.assertRaises(ValueError):
                s.msg_delivery_status('msg1234xyz')

    def test_msg_cost(self):
        s = BulkSMS('foo')
        with mock.patch('tattler.server.sendable.bulksms.urllib.request') as mreq:
            # invalid response
            cost_want = 123.43
            msg = """[{"status": {"creditCost": %s}}]""" % cost_want
            mreq.urlopen().__enter__().read.return_value = msg.encode()
            cost_have = s.msg_cost('msg1234xyz')
            self.assertEqual(cost_want, cost_have)

    def test_msg_cost_errors(self):
        s = BulkSMS('foo')
        with mock.patch('tattler.server.sendable.bulksms.urllib.request') as mreq:
            # invalid response
            err = urllib.error.URLError("Connection refused")
            mreq.urlopen().__enter__().read.side_effect = err
            with self.assertRaises(type(err)):
                s.msg_cost('msg1234xyz')
            # valid response, invalid JSON
            mreq.urlopen().__enter__().read.return_value = b"""invalid [ json junk }"""
            mreq.urlopen().__enter__().read.side_effect = None
            with self.assertRaises(ValueError):
                s.msg_cost('msg1234xyz')
            # valid response, valid JSON, missing fields
            mreq.urlopen().__enter__().read.return_value = b"""[]"""
            mreq.urlopen().__enter__().read.side_effect = None
            with self.assertRaises(ValueError):
                s.msg_cost('msg1234xyz')

if __name__ == '__main__':
    unittest.main()