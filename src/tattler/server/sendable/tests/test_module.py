import os
import unittest
from unittest import mock

from pathlib import Path

# suppress warning when SMSSendable is imported
os.environ['TATTLER_BULKSMS_TOKEN'] = 'A:B'

from tattler.server import pluginloader
from tattler.server import sendable
from tattler.server.sendable.vector_text import TextSendable


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

    def test_available_vectors_includes_plugin_declared(self):
        """available_vectors() includes vectors declared by loaded delivery backend plug-ins along with built-ins"""
        backend = mock.MagicMock()
        backend.vector.return_value = 'signal'
        with mock.patch.dict(pluginloader.loaded_plugins, {'deliverybackend': {'SignalBackend': backend}}, clear=True):
            self.assertIn('signal', sendable.available_vectors())
            self.assertIn('sms', sendable.available_vectors())
            self.assertIn('email', sendable.available_vectors())

    def test_get_vector_class_serves_plugin_declared_vector(self):
        """get_vector_class() builds a TextSendable bound to a vector that only a plug-in declares"""
        backend = mock.MagicMock()
        backend.vector.return_value = 'signal'
        with mock.patch.dict(pluginloader.loaded_plugins, {'deliverybackend': {'SignalBackend': backend}}, clear=True):
            with mock.patch.dict(sendable._dynamic_sendables, clear=True):
                vclass = sendable.get_vector_class('signal')
                self.assertTrue(issubclass(vclass, TextSendable))
                self.assertEqual('signal', vclass.vector())
                self.assertIs(vclass, sendable.get_vector_class('signal'))

    def test_register_vector_sendable(self):
        """register_vector_sendable() makes a dedicated class available under the vector it declares"""
        class FaxSendable(TextSendable):
            vector_name = 'fax'
        with mock.patch.dict(sendable.vector_sendables):
            sendable.register_vector_sendable(FaxSendable)
            self.assertIn('fax', sendable.available_vectors())
            self.assertTrue(issubclass(sendable.get_vector_class('fax'), FaxSendable))

    def test_register_sendable_base_composes_every_vector(self):
        """register_sendable_base() composes registered and plug-in-declared vector classes with the new base"""
        class CustomBase(sendable.Sendable):
            pass
        backend = mock.MagicMock()
        backend.vector.return_value = 'signal'
        with mock.patch.dict(sendable.vector_sendables):
            with mock.patch.object(sendable, '_sendable_base', sendable._sendable_base):
                with mock.patch.dict(pluginloader.loaded_plugins, {'deliverybackend': {'SignalBackend': backend}}, clear=True):
                    with mock.patch.dict(sendable._dynamic_sendables, clear=True):
                        sendable.register_sendable_base(CustomBase)
                        for vname in ('sms', 'email', 'signal'):
                            vclass = sendable.get_vector_class(vname)
                            self.assertTrue(issubclass(vclass, CustomBase), msg=f"Vector {vname} class lacks the registered base.")
                        self.assertEqual('SMSSendable', sendable.get_vector_class('sms').__name__)
