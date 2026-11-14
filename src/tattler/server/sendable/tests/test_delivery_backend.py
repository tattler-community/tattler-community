"""Tests for the delivery backend interface and generic backend selection"""

import unittest
from unittest import mock

from tattler.server import pluginloader
from tattler.server.sendable import delivery_backend
from tattler.server.sendable.delivery_backend import DeliveryBackend
from tattler.server.sendable.backends.bulksms_tattler_plugin import BulkSMSBackend
from tattler.server.sendable.backends.bulkgate_tattler_plugin import BulkGateBackend


class TestDeliveryBackendInterface(unittest.TestCase):
    def test_envvar_naming(self):
        """envvar() namespaces settings under the backend's own name"""
        self.assertEqual(BulkSMSBackend.envvar('TOKEN'), 'TATTLER_BULKSMS_TOKEN')
        self.assertEqual(BulkGateBackend.envvar('TOKEN'), 'TATTLER_BULKGATE_TOKEN')

    def test_available_reflects_configuration(self):
        """available() is True iff the backend's configuration validates"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas'}.get(x, None)
            self.assertTrue(BulkSMSBackend.available())
            self.assertFalse(BulkGateBackend.available())
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': 'malformed'}.get(x, None)
            self.assertFalse(BulkSMSBackend.available())

    def test_default_name_from_class(self):
        """name() defaults to the class name lowercased, without any 'backend' suffix"""
        self.assertEqual(BulkSMSBackend.name(), 'bulksms')
        self.assertEqual(BulkGateBackend.name(), 'bulkgate')

    def test_setup_validates_configuration(self):
        """setup() raises at plug-in load iff the backend's configuration is missing or invalid"""
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: None
            with self.assertRaises(ValueError):
                BulkSMSBackend().setup()
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas'}.get(x, None)
            BulkSMSBackend().setup()

    def test_setup_tells_unconfigured_from_misconfigured(self):
        """setup() raises PluginNotConfigured iff no setting is provided, plain ValueError if incomplete or malformed"""
        class TwoSettingsBackend(DeliveryBackend):
            required_settings = {'USER': [True, None], 'TOKEN': [True, None]}
            @classmethod
            def vector(cls) -> str:
                return 'sms'
        with mock.patch('tattler.server.sendable.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: None
            with self.assertRaises(pluginloader.PluginNotConfigured):
                TwoSettingsBackend().setup()
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_TWOSETTINGS_USER': 'foo'}.get(x, None)
            with self.assertRaises(ValueError) as err:
                TwoSettingsBackend().setup()
            self.assertNotIsInstance(err.exception, pluginloader.PluginNotConfigured)
            self.assertIn('TATTLER_TWOSETTINGS_TOKEN', str(err.exception))
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKGATE_TOKEN': 'malformed'}.get(x, None)
            with self.assertRaises(ValueError) as err:
                BulkGateBackend().setup()
            self.assertNotIsInstance(err.exception, pluginloader.PluginNotConfigured)

    def test_default_cost_and_delivery_status(self):
        """cost() and delivery_status() default to no data for backends without the facility"""
        backend = BulkGateBackend()
        self.assertIsNone(backend.cost(['+123456789'], 'hello'))
        self.assertEqual({}, backend.delivery_status(mock.Mock()))

    def test_default_validate_recipient_accepts_anything(self):
        """Default validate_recipient() accepts any recipient unchanged"""
        for rcpt in ['+19876543210', 'anything', '']:
            self.assertEqual(rcpt, BulkGateBackend.validate_recipient(rcpt))


class TestGetBackends(unittest.TestCase):
    def test_returns_configured_backends_of_the_requested_vector(self):
        """get_backends() returns loaded backend instances declaring the requested vector"""
        bulksms, bulkgate = BulkSMSBackend(), BulkGateBackend()
        with mock.patch.dict(pluginloader.loaded_plugins, {'deliverybackend': {'BulkSMSBackend': bulksms, 'BulkGateBackend': bulkgate}}, clear=True):
            self.assertEqual(delivery_backend.get_backends('sms'), [bulkgate, bulksms])

    def test_excludes_plugins_of_other_vectors(self):
        """get_backends() only includes backends declaring the requested vector"""
        bulksms = BulkSMSBackend()
        othervector = mock.Mock()
        othervector.name.return_value = 'othervector'
        othervector.vector.return_value = 'telegram'
        with mock.patch.dict(pluginloader.loaded_plugins, {'deliverybackend': {'BulkSMSBackend': bulksms, 'OtherVectorBackend': othervector}}, clear=True):
            self.assertEqual(delivery_backend.get_backends('sms'), [bulksms])

    def test_raises_with_each_backends_problem_when_none_configured(self):
        """get_backends() raises with every same-vector backend's problem when none is configured"""
        with mock.patch.dict(pluginloader.loaded_plugins, {}, clear=True):
            with mock.patch.dict(pluginloader.loaded_plugin_errors, {'deliverybackend': {
                'BulkSMSBackend': (BulkSMSBackend, "Required setting 'TATTLER_BULKSMS_TOKEN' is missing."),
                'BulkGateBackend': (BulkGateBackend, "Required setting 'TATTLER_BULKGATE_TOKEN' is missing."),
            }}, clear=True):
                with self.assertRaises(ValueError) as err:
                    delivery_backend.get_backends('sms')
                self.assertIn('TATTLER_BULKSMS_TOKEN', str(err.exception))
                self.assertIn('TATTLER_BULKGATE_TOKEN', str(err.exception))

    def test_error_detail_excludes_other_vectors(self):
        """The aggregated error only cites problems of backends declaring the requested vector"""
        with mock.patch.dict(pluginloader.loaded_plugins, {}, clear=True):
            with mock.patch.dict(pluginloader.loaded_plugin_errors, {'deliverybackend': {
                'BulkSMSBackend': (BulkSMSBackend, "Required setting 'TATTLER_BULKSMS_TOKEN' is missing."),
            }}, clear=True):
                with self.assertRaises(ValueError) as err:
                    delivery_backend.get_backends('telegram')
                self.assertNotIn('TATTLER_BULKSMS_TOKEN', str(err.exception))


class TestPluginVectors(unittest.TestCase):
    def test_lists_vectors_declared_by_loaded_backends(self):
        """plugin_vectors() returns the set of vectors declared by loaded backends"""
        signal = mock.Mock()
        signal.vector.return_value = 'signal'
        with mock.patch.dict(pluginloader.loaded_plugins, {'deliverybackend': {'BulkSMSBackend': BulkSMSBackend(), 'SignalBackend': signal}}, clear=True):
            self.assertEqual({'sms', 'signal'}, delivery_backend.plugin_vectors())

    def test_empty_without_loaded_backends(self):
        """plugin_vectors() returns no vectors when no backend is loaded"""
        with mock.patch.dict(pluginloader.loaded_plugins, {}, clear=True):
            self.assertEqual(set(), delivery_backend.plugin_vectors())


class TestNativeBackendsAreDiscoverable(unittest.TestCase):
    def test_shipped_backends_are_found_among_native_plugin_paths(self):
        """Backends shipped with tattler are found by scanning pluginloader's native plug-in paths"""
        candidates = pluginloader.load_candidate_modules([str(p) for p in pluginloader.native_plugin_paths])
        self.assertIn('bulksms_tattler_plugin', candidates)
        self.assertIn('bulkgate_tattler_plugin', candidates)


if __name__ == '__main__':
    unittest.main()
