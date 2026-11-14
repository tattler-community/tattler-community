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
        s = SMSSendable('event', ['+123456789'])
        self.assertIsNotNone(s)

    def test_assert_prefix_plus_zero_equivalent(self):
        """Constructor accepts mobile numbers with plus or 00 prefix"""
        sp = SMSSendable('event', ['+123456789'])
        self.assertIsNotNone(sp)
        s0 = SMSSendable('event', ['00123456789'])
        self.assertIsNotNone(s0)
        self.assertEqual(s0.recipients, sp.recipients)

    def test_invalid_recipient_rejected(self):
        """SMSSendable constructor raises iff given recipient is malformed"""
        with self.assertRaises(ValueError):
            SMSSendable('event', ['asd'])

    def test_validate_configuration_requires_a_configured_backend(self):
        """validate_configuration() raises iff no sms delivery backend is configured, and propagates why"""
        with mock.patch('tattler.server.sendable.vector_sms.delivery_backend.get_backends') as mgetbackends:
            mgetbackends.side_effect = ValueError("No sms backend is configured. bulksms: Required setting 'TATTLER_BULKSMS_TOKEN' is missing.")
            with self.assertRaises(ValueError) as err:
                SMSSendable.validate_configuration()
            self.assertIn('TATTLER_BULKSMS_TOKEN', str(err.exception))

    def test_validate_configuration_accepts_configured_backends(self):
        """validate_configuration() succeeds once at least one sms delivery backend is configured"""
        with mock.patch('tattler.server.sendable.vector_sms.delivery_backend.get_backends') as mgetbackends:
            mgetbackends.return_value = [mock.Mock(), mock.Mock()]
            SMSSendable.validate_configuration()

    def test_send_failover_to_next_backend(self):
        """send() tries backends in order and delivers with the first that accepts the message"""
        with mock.patch('tattler.server.sendable.vector_sms.delivery_backend.get_backends') as mgetbackends:
            with mock.patch('tattler.server.sendable.vector_sms.vector_sendable.Sendable.content'):
                failing, working = mock.MagicMock(), mock.MagicMock()
                failing.send.side_effect = RuntimeError('gateway down')
                mgetbackends.return_value = [failing, working]
                snd = SMSSendable('event', ['+123456789'])
                snd.send()
                failing.send.assert_called_once()
                working.send.assert_called_once()

    def test_send_all_backends_fail(self):
        """send() raises iff no configured backend accepts the message"""
        with mock.patch('tattler.server.sendable.vector_sms.delivery_backend.get_backends') as mgetbackends:
            with mock.patch('tattler.server.sendable.vector_sms.vector_sendable.Sendable.content'):
                failing1, failing2 = mock.MagicMock(), mock.MagicMock()
                failing1.send.side_effect = RuntimeError('gateway down')
                failing2.send.side_effect = RuntimeError('auth rejected')
                mgetbackends.return_value = [failing1, failing2]
                snd = SMSSendable('event', ['+123456789'])
                with self.assertRaises(ValueError):
                    snd.send()
                failing1.send.assert_called_once()
                failing2.send.assert_called_once()

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
        with mock.patch('tattler.server.sendable.vector_sms.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.vector_sms.delivery_backend.get_backends') as mgetbackends:
                with mock.patch('tattler.server.sendable.vector_sms.vector_sendable.Sendable.content'):
                    mgetenv.side_effect = lambda x, y=None: {
                        'TATTLER_SMS_SENDER': '+12345678,+41234567,+41987654311',
                        'TATTLER_BULKSMS_TOKEN': '12:aas'
                    }.get(x, os.getenv(x, y))
                    mbackend = mock.MagicMock()
                    mgetbackends.return_value = [mbackend]
                    snd = SMSSendable('event', ['+123456789', '+16548351', '+4156894562'])
                    snd.send()
                    self.assertEqual(2, mbackend.send.call_count)
                    self.assertIn('sender', mbackend.send.call_args_list[0].kwargs)
                    self.assertIn('sender', mbackend.send.call_args_list[1].kwargs)
                    senders = {x.kwargs['sender']: x[0][0] for x in mbackend.send.call_args_list}
                    self.assertEqual(senders, {
                        '+12345678': {'+123456789', '+16548351'},
                        '+41234567': {'+4156894562'}
                    })

    def test_new_filename_scheme_prevails(self):
        """If both files body.html and body_plain exist, the former (newer) is picked"""
        e = SMSSendable('event_with_old_and_new_filename_schemes', ['+123456789'], template_base=tbase_originalnaming_path)
        self.assertIn('new filename scheme', e.content(context={'one': '#1234#'}))
        self.assertNotIn('old filename scheme', e.content(context={'one': '#1234#'}))


if __name__ == '__main__':
    unittest.main()
