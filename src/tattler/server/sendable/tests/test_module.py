import os
import unittest
from unittest import mock

from pathlib import Path

# suppress warning when SMSSendable is imported
os.environ['TATTLER_BULKSMS_TOKEN'] = 'A:B'

from tattler.server import sendable


class UtilsTest(unittest.TestCase):
    """Test utility functions exposed by module itself"""
    
    template_base = Path() / 'fixtures' / 'templates'
    blacklist_path = Path('fixtures') / 'blacklist.txt'
    recipients = {
        'email': ['support@test123.com'],
        'sms': ['+11234567898', '00417689876']
    }

    def test_make_notification_email(self):
        n = sendable.make_notification('email', 'event_with_email_and_sms', ['u1@x.com'], template_base=self.template_base)
        self.assertEqual(n.vector(), 'email')
        self.assertEqual({'u1@x.com'}, n.delivery_recipients('production'))
        n = sendable.make_notification('sms', 'event_with_email_and_sms', ['+12345'], template_base=self.template_base)
        self.assertEqual(n.vector(), 'sms')
        self.assertEqual({'+12345'}, n.delivery_recipients('production'))
    
    def test_make_notification_missing_vector(self):
        with self.assertRaises(ValueError):
            n = sendable.make_notification('inexvec', 'event_with_email_and_sms', ['u1@x.com'], template_base=self.template_base)

    def test_send_notification_sends(self):
        with mock.patch('tattler.server.sendable.Sendable.send') as msend:
            ctx = {'a': 1, 'b': 2}
            sendable.send_notification('email', 'event_with_email_and_sms', ['u1@x.com'], context=ctx, mode='debug')
            self.assertEqual(msend.call_count, 1)
            self.assertIn('context', msend.call_args.kwargs)
            self.assertEqual(ctx, msend.call_args.kwargs['context'])
            self.assertIn('mode', msend.call_args.kwargs)
            self.assertEqual('debug', msend.call_args.kwargs['mode'])
    
    def test_send_notification_debug_includes_debug_address(self):
        with mock.patch('tattler.server.sendable.Sendable.do_send') as msend:
            sendable.send_notification('email', 'event_with_email_and_sms', ['u1@x.com'], mode='debug')

    def test_delivery_works_if_given_blacklist_missing(self):
        with mock.patch('tattler.server.sendable.Sendable.send') as msend:
            sendable.send_notification('email', 'event_with_email_and_sms', ['u1@x.com'], mode='debug', blacklist='inexistent-file-1234.txt')
            self.assertEqual(msend.call_count, 1)
