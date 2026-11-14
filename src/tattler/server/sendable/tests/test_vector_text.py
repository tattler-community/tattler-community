"""Tests for TextSendable, the generic sendable for plug-in-declared vectors"""

import unittest
from unittest import mock
from pathlib import Path

from tattler.server import pluginloader
from tattler.server import sendable
from tattler.server.sendable.vector_text import TextSendable


def make_mock_backend(name: str='mockprovider', vector: str='signal') -> mock.MagicMock:
    """Return a mock delivery backend declaring the given name and vector, accepting any recipient"""
    backend = mock.MagicMock()
    backend.name.return_value = name
    backend.vector.return_value = vector
    backend.validate_recipient.side_effect = lambda r: r
    return backend


class SignalSendable(TextSendable):
    vector_name = 'signal'


class TextSendableTest(unittest.TestCase):
    template_base = Path(__file__).parent / 'fixtures' / 'templates'

    def test_vector_requires_binding(self):
        """vector() rejects usage without a vector name bound to the class"""
        with self.assertRaises(AssertionError):
            TextSendable.vector()

    def test_validate_recipient_accepts_iff_any_backend_accepts(self):
        """A recipient is valid iff some backend of the vector accepts it, and the first accepting backend normalizes it"""
        rejecting, accepting = make_mock_backend('rejecting'), make_mock_backend('accepting')
        rejecting.validate_recipient.side_effect = ValueError('bad address')
        accepting.validate_recipient.side_effect = lambda r: r.replace('00', '+', 1)
        with mock.patch('tattler.server.sendable.vector_text.delivery_backend.get_backends') as mgetbackends:
            mgetbackends.return_value = [rejecting, accepting]
            want_recipients = ['+123456']
            snd = SignalSendable('event', ['00123456'])
            self.assertEqual(want_recipients, snd.recipients)

    def test_validate_recipient_rejected_by_all_backends(self):
        """Recipient construction raises iff every backend of the vector rejects the recipient, citing each backend's reason"""
        rejecting1, rejecting2 = make_mock_backend('rejecting1'), make_mock_backend('rejecting2')
        rejecting1.validate_recipient.side_effect = ValueError('not a phone number')
        rejecting2.validate_recipient.side_effect = ValueError('not a username')
        with mock.patch('tattler.server.sendable.vector_text.delivery_backend.get_backends') as mgetbackends:
            mgetbackends.return_value = [rejecting1, rejecting2]
            with self.assertRaises(ValueError) as err:
                SignalSendable('event', ['@!#'])
            self.assertIn('rejecting1', str(err.exception))
            self.assertIn('rejecting2', str(err.exception))

    def test_send_notification_delivers_arbitrary_vector_via_backend(self):
        """send_notification() delivers a vector known only to a plug-in backend, end to end"""
        backend = make_mock_backend('signalprovider', 'signal')
        with mock.patch.dict(pluginloader.loaded_plugins, {'deliverybackend': {'SignalBackend': backend}}, clear=True):
            with mock.patch.dict(sendable._dynamic_sendables, clear=True):
                sendable.send_notification('signal', 'event_with_signal', ['sig-user-1'], context={'one': '#1234#'}, template_base=self.template_base, mode='production')
                backend.send.assert_called_once()
                sent_recipients, sent_body = backend.send.call_args.args[:2]
                self.assertEqual({'sig-user-1'}, set(sent_recipients))
                self.assertIn('#1234#', sent_body)


if __name__ == '__main__':
    unittest.main()
