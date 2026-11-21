"""Tests for the bulkgate SMS backend"""

import unittest
from unittest import mock
import json

from tattler.server.sendable.backends.bulkgate_tattler_plugin import BulkGateBackend


def mock_response(payload):
    """Build a context-manager mock mimicking urlopen's response with a JSON payload"""
    resp = mock.MagicMock()
    resp.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    return resp


class TestBulkGateBackend(unittest.TestCase):
    def test_get_auth_valid(self):
        """get_auth() returns the application credential pair split at the first ':'"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKGATE_TOKEN': 'appid:app:token'}.get(x, None)
            self.assertEqual(BulkGateBackend().get_auth(), ('appid', 'app:token'))

    def test_get_auth_malformed(self):
        """get_auth() raises iff the configured token lacks the ':' separator"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKGATE_TOKEN': 'foobar'}.get(x, None)
            with self.assertRaises(ValueError):
                BulkGateBackend().get_auth()

    def test_send_one_request_per_recipient(self):
        """send() posts one request per recipient and collects each sms_id"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.backends.bulkgate_tattler_plugin.urllib.request.urlopen') as murlopen:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKGATE_TOKEN': 'id:tok'}.get(x, None)
                murlopen.side_effect = [
                    mock_response({'data': {'status': 'accepted', 'sms_id': 'sid1', 'number': '123'}}),
                    mock_response({'data': {'status': 'accepted', 'sms_id': 'sid2', 'number': '456'}}),
                ]
                res = BulkGateBackend().send(['+123', '+456'], 'hello')
                self.assertEqual(res.recipient_ids, {'+123': 'sid1', '+456': 'sid2'})
                self.assertEqual(2, murlopen.call_count)
                sent = json.loads(murlopen.call_args_list[0][0][0].data.decode())
                self.assertEqual(sent['application_id'], 'id')
                self.assertEqual(sent['application_token'], 'tok')
                self.assertEqual(sent['number'], '123')
                self.assertEqual(sent['text'], 'hello')

    def test_send_sender_and_unicode(self):
        """send() requests the given sender id and flags unicode for non-ascii content"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.backends.bulkgate_tattler_plugin.urllib.request.urlopen') as murlopen:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKGATE_TOKEN': 'id:tok'}.get(x, None)
                murlopen.return_value = mock_response({'data': {'sms_id': 'sid1'}})
                BulkGateBackend().send(['+123'], 'Glückwunsch!', sender='+789')
                sent = json.loads(murlopen.call_args[0][0].data.decode())
                self.assertEqual(sent['unicode'], '1')
                self.assertEqual(sent['sender_id'], 'gOwn')
                self.assertEqual(sent['sender_id_value'], '789')

    def test_send_text_sender(self):
        """send() requests a text sender iff the given sender id is an alphanumeric name"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.backends.bulkgate_tattler_plugin.urllib.request.urlopen') as murlopen:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKGATE_TOKEN': 'id:tok'}.get(x, None)
                murlopen.return_value = mock_response({'data': {'sms_id': 'sid1'}})
                BulkGateBackend().send(['+123'], 'hello', sender='Acme')
                sent = json.loads(murlopen.call_args[0][0].data.decode())
                self.assertEqual(sent['sender_id'], 'gText')
                self.assertEqual(sent['sender_id_value'], 'Acme')

    def test_send_number_sender_zero_prefix_equivalent(self):
        """send() requests the same own-number sender, stripped of its prefix, whether given with plus or 00 prefix"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.backends.bulkgate_tattler_plugin.urllib.request.urlopen') as murlopen:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKGATE_TOKEN': 'id:tok'}.get(x, None)
                murlopen.return_value = mock_response({'data': {'sms_id': 'sid1'}})
                want_params = {'sender_id': 'gOwn', 'sender_id_value': '789'}
                for sender in ['+789', '00789']:
                    BulkGateBackend().send(['+123'], 'hello', sender=sender)
                    sent = json.loads(murlopen.call_args[0][0].data.decode())
                    self.assertEqual({k: sent[k] for k in want_params}, want_params, msg=sender)

    def test_send_no_sender(self):
        """send() leaves the sender to the provider's default iff no sender id is given"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.backends.bulkgate_tattler_plugin.urllib.request.urlopen') as murlopen:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKGATE_TOKEN': 'id:tok'}.get(x, None)
                murlopen.return_value = mock_response({'data': {'sms_id': 'sid1'}})
                BulkGateBackend().send(['+123'], 'hello')
                sent = json.loads(murlopen.call_args[0][0].data.decode())
                self.assertNotIn('sender_id', sent)
                self.assertNotIn('sender_id_value', sent)

    def test_send_invalid_sender_rejected(self):
        """send() raises before contacting the provider iff the sender id is neither a number nor a name"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.backends.bulkgate_tattler_plugin.urllib.request.urlopen') as murlopen:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKGATE_TOKEN': 'id:tok'}.get(x, None)
                for sender in ['12345', '079 123 45 67', 'AcmeCorporation']:
                    with self.assertRaises(ValueError, msg=sender):
                        BulkGateBackend().send(['+123'], 'hello', sender=sender)
                murlopen.assert_not_called()

    def test_send_rejected(self):
        """send() raises iff the provider returns an error instead of message data"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.backends.bulkgate_tattler_plugin.urllib.request.urlopen') as murlopen:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKGATE_TOKEN': 'id:tok'}.get(x, None)
                murlopen.return_value = mock_response({'type': 'invalid_phone_number', 'code': 400, 'error': 'Invalid phone number'})
                with self.assertRaises(ValueError):
                    BulkGateBackend().send(['+123'], 'hello')


if __name__ == '__main__':
    unittest.main()
