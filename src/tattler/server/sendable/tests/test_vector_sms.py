"""Tests for SMSSendable"""

import unittest
from unittest import mock
import os
from pathlib import Path

from tattler.server.sendable import vector_sms              # for patching
from tattler.server.sendable.vector_sms import SMSSendable

tbase_originalnaming_path = Path(__file__).parent / 'fixtures' / 'templates_originalnaming'


class TestVectorSMS(unittest.TestCase):
    def test_construction(self):
        """Constructor succeeds if valid data is passed to it"""
        with mock.patch('tattler.server.sendable.vector_sms.getenv') as mgetenv:
            mgetenv.side_effect = lambda k, v: { 'TATTLER_BULKSMS_TOKEN': '3456789'}.get(k, os.getenv(k, v))
            s = SMSSendable('event', ['+123456789'])
            self.assertIsNotNone(s)
    
    def test_assert_prefix_plus_zero_equivalent(self):
        """Constructor accepts mobile numbers with plus or 00 prefix"""
        with mock.patch('tattler.server.sendable.vector_sms.getenv') as mgetenv:
            mgetenv.side_effect = lambda k, v: { 'TATTLER_BULKSMS_TOKEN': '3456789'}.get(k, os.getenv(k, v))
            sp = SMSSendable('event', ['+123456789'])
            self.assertIsNotNone(sp)
            s0 = SMSSendable('event', ['00123456789'])
            self.assertIsNotNone(s0)
            self.assertEqual(s0.recipients, sp.recipients)

    def test_invalid_recipient_rejected(self):
        """SMSSendable constructor raises iff given recipient is malformed"""
        with mock.patch('tattler.server.sendable.vector_sms.getenv') as mgetenv:
            mgetenv.side_effect = lambda k, v: { 'TATTLER_BULKSMS_TOKEN': '3456789'}.get(k, os.getenv(k, v))
            with self.assertRaises(ValueError):
                SMSSendable('event', ['asd'])
    
    def test_invalid_auth_data(self):
        """SMSSendable constructor raises iff TATTLER_BULKSMS_TOKEN malformed"""
        with mock.patch('tattler.server.sendable.vector_sms.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.vector_sms.BulkSMS') as msms:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': 'foobar'}.get(x, os.getenv(x, y))
                with self.assertRaises(ValueError):
                    s0 = SMSSendable('event', ['00123456789'])
                    s0.get_sms_server()

    def test_validate_configuration_token(self):
        """validate_configuration() fails iff settings missing or malformed"""
        with mock.patch('tattler.server.sendable.vector_sms.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': None}.get(x, os.getenv(x, y))
            with self.assertRaises(ValueError) as err:
                SMSSendable.validate_configuration()
            self.assertIn('TATTLER_BULKSMS_TOKEN', str(err.exception))
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': 'invalid string; 123'}.get(x, os.getenv(x, y))
            with self.assertRaises(ValueError) as err:
                SMSSendable.validate_configuration()
            self.assertIn('TATTLER_BULKSMS_TOKEN', str(err.exception))
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '123:afadad121435'}.get(x, os.getenv(x, y))
            SMSSendable.validate_configuration()

    def test_sender_multiple_values_default(self):
        """sender() returns the first entry of multiple if no recipient or no shared prefix with it"""
        with mock.patch('tattler.server.sendable.vector_sms.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_SMS_SENDER': '+12345678,+41234567'}.get(x, os.getenv(x, y))
            self.assertEqual(SMSSendable.sender(), '+12345678')
            self.assertEqual(SMSSendable.sender('+23456'), '+12345678')

    def test_sender_multiple_values_longest_prefix(self):
        """sender() returns the entry with longest shared prefix if matching recipient given"""
        with mock.patch('tattler.server.sendable.vector_sms.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_SMS_SENDER': '+12345678,+41234567,+41987654311'}.get(x, os.getenv(x, y))
            self.assertEqual(SMSSendable.sender('+1674590832'), '+12345678')
            self.assertEqual(SMSSendable.sender('+34569871'), '+12345678')
            self.assertEqual(SMSSendable.sender('+432145'), '+41234567')
            self.assertEqual(SMSSendable.sender('+4191'), '+41987654311')
            self.assertEqual(SMSSendable.sender('+41432'), '+41234567')

    def test_send_splits_by_senderid(self):
        """send() calls one delivery for each different sender_id, when multiple are required"""
        with mock.patch('tattler.server.sendable.vector_sms.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.vector_sms.vector_sendable.getenv') as mgetenv2:
                with mock.patch('tattler.server.sendable.vector_sms.BulkSMS') as msms:
                    with mock.patch('tattler.server.sendable.vector_sms.vector_sendable.Sendable.content'):
                        mgetenv.side_effect = lambda x, y=None: {
                            'TATTLER_SMS_SENDER': '+12345678,+41234567,+41987654311',
                            'TATTLER_BULKSMS_TOKEN': '12:aas'
                        }.get(x, os.getenv(x, y))
                        mgetenv2.side_effect = mgetenv.side_effect
                        snd = SMSSendable('event', ['+123456789', '+16548351', '+4156894562'])
                        snd.send()
                        msms.assert_called()
                        self.assertEqual(2, msms.return_value.send.call_count)
                        self.assertIn('sender', msms.return_value.send.call_args_list[0].kwargs)
                        self.assertIn('sender', msms.return_value.send.call_args_list[1].kwargs)
                        senders = {x.kwargs['sender']:x[0][0] for x in msms.return_value.send.call_args_list}
                        self.assertEqual(senders, {
                            '+12345678': {'+123456789', '+16548351'},
                            '+41234567': {'+4156894562'}
                        })

    def test_validate_configuration_sender(self):
        """validate_configuration() fails iff settings missing or malformed"""
        with mock.patch('tattler.server.sendable.vector_sms.vector_sendable.getenv') as mgetenv:
            # TATTLER_SMS_SENDER not provided => ok
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas'}.get(x, os.getenv(x, y))
            SMSSendable.validate_configuration()
            # TATTLER_SMS_SENDER provided, malformed => error
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas', 'TATTLER_SMS_SENDER': 'asd'}.get(x, os.getenv(x, y))
            with self.assertRaises(ValueError) as err:
                SMSSendable.validate_configuration()
            self.assertIn('TATTLER_SMS_SENDER', str(err.exception))
            # TATTLER_SMS_SENDER provided, well-formed => ok
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas', 'TATTLER_SMS_SENDER': '+12345'}.get(x, os.getenv(x, y))
            SMSSendable.validate_configuration()

    def test_new_filename_scheme_prevails(self):
        """If both files body.html and body_plain exist, the former (newer) is picked"""
        e = SMSSendable('event_with_old_and_new_filename_schemes', ['+123456789'], template_base=tbase_originalnaming_path)
        self.assertIn('new filename scheme', e.content(context={'one': '#1234#'}))
        self.assertNotIn('old filename scheme', e.content(context={'one': '#1234#'}))


if __name__ == '__main__':
    unittest.main()
