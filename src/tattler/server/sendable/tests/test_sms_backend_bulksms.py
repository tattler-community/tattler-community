"""Tests for the bulksms SMS backend"""

import unittest
from unittest import mock

from tattler.server.sendable.delivery_backend import SendResult
from tattler.server.sendable.backends.bulksms_tattler_plugin import BulkSMSBackend


class TestBulkSMSBackend(unittest.TestCase):
    def test_get_auth_valid(self):
        """get_auth() returns the token pair split at the first ':'"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': 'tid:se:cret'}.get(x, None)
            self.assertEqual(BulkSMSBackend().get_auth(), ('tid', 'se:cret'))

    def test_get_auth_malformed(self):
        """get_auth() raises iff the configured token lacks the ':' separator"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': 'foobar'}.get(x, None)
            with self.assertRaises(ValueError):
                BulkSMSBackend().get_auth()

    def test_send_maps_recipients_to_message_ids(self):
        """send() returns one provider message id per recipient"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.backends.bulksms_tattler_plugin.BulkSMS') as msms:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas'}.get(x, None)
                msms.return_value.send.return_value = ['id1', 'id2']
                res = BulkSMSBackend().send(['+123', '+456'], 'hello', sender='+789', priority=1)
                msms.return_value.send.assert_called_once_with(['+123', '+456'], 'hello', sender='+789', priority=1)
                self.assertEqual(res.recipient_ids, {'+123': 'id1', '+456': 'id2'})

    def test_delivery_status_normalized(self):
        """delivery_status() maps provider states onto the normalized vocabulary, with cost"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.backends.bulksms_tattler_plugin.BulkSMS') as msms:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas'}.get(x, None)
                msms.return_value.msg_status.side_effect = [
                    {'status': {'type': 'DELIVERED'}, 'creditCost': 1.0},
                    {'status': {'type': 'FAILED'}},
                    {'status': {'type': 'SCHEDULED'}},
                ]
                res = BulkSMSBackend().delivery_status(SendResult(recipient_ids={'+1': 'a', '+2': 'b', '+3': 'c'}))
                self.assertEqual(res['+1'].status, 'delivered')
                self.assertEqual(res['+1'].cost, 1.0)
                self.assertEqual(res['+2'].status, 'failed')
                self.assertEqual(res['+3'].status, 'pending')

    def test_delivery_status_lookup_failure(self):
        """delivery_status() reports 'unknown' for recipients whose lookup failed, without raising"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.backends.bulksms_tattler_plugin.BulkSMS') as msms:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas'}.get(x, None)
                msms.return_value.msg_status.side_effect = RuntimeError('boom')
                res = BulkSMSBackend().delivery_status(SendResult(recipient_ids={'+1': 'a'}))
                self.assertEqual(res['+1'].status, 'unknown')


if __name__ == '__main__':
    unittest.main()
