import unittest
from unittest import mock
import os
import random

from tattler.server import pluginloader

def get_addressbook_retval():
    return {
            'email': f'foo{random.randint(1, 10000)}@bar.com',
            'mobile': '+' + ''.join([str(random.randint(1, 9)) for x in range(10)]),
            'account_type': random.choice(['free', 'pro']),
            'first_name': f'Name{random.randint(1, 1000)}',
        }


class PluginLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plugin_paths = [os.path.join('fixtures', 'plugins')]
        return super().setUp()

    def test_missing_path_loads_no_plugins(self):
        """If no path with plugins is provided, then no plugin is loaded"""
        lplugs = pluginloader.init(self.plugin_paths)
        self.assertFalse(lplugs)
    
    def test_plugins_loaded(self):
        """If a path with plugins is provided, then all its contained plugins are loaded."""
        plugcand = pluginloader.load_candidate_modules(self.plugin_paths)
        self.assertEqual(2, len(plugcand))
        plugmap = pluginloader.load_plugins(plugcand)
        loaded_plugin_categories = set(plugmap.keys())
        self.assertEqual({'context'}, loaded_plugin_categories)
        self.assertEqual({'Test1TattlerPlugin', 'Test2TattlerPlugin'}, plugmap['context'].keys())
    
    def test_plugin_category_rejects_invalid_classes(self):
        """Classes that do not inherit from tattler interfaces are not recognized as plugins"""
        self.assertIsNone(pluginloader.plugin_category('RuntimeError', RuntimeError))
        self.assertIsNone(pluginloader.plugin_category('TestCase', unittest.TestCase))
    
    def test_plugin_category_rejects_self_classes(self):
        """Classes that are tattler interfaces themselves are not recognized as plugins"""
        self.assertIsNone(pluginloader.plugin_category('TattlerPlugin', pluginloader.TattlerPlugin))
        self.assertIsNone(pluginloader.plugin_category('AddressbookPlugin', pluginloader.AddressbookPlugin))
        self.assertIsNone(pluginloader.plugin_category('ContextTattlerPlugin', pluginloader.ContextTattlerPlugin))

    def test_plugin_category_recognizes_valid_classes(self):
        """Classes that are tattler interfaces themselves are not recognized as plugins"""
        class Foo(pluginloader.TattlerPlugin): pass
        class FooAddr(pluginloader.AddressbookPlugin): pass
        class FooCtx(pluginloader.ContextTattlerPlugin): pass

        self.assertIsNone(pluginloader.plugin_category('Foo', Foo))
        self.assertEqual('addressbook', pluginloader.plugin_category('FooAddr', FooAddr))
        self.assertEqual('context', pluginloader.plugin_category('FooCtx', FooCtx))

    def test_only_valid_plugins_are_initialized(self):
        """Only plugins respecting their interface are loaded, and have their setup() function called"""
        with mock.patch('tattler.server.pluginloader.load_candidate_modules') as mcandmod:
            with mock.patch('tattler.server.pluginloader.importlib'):
                with mock.patch('tattler.server.pluginloader.plugin_category') as misplug:
                    with mock.patch('tattler.server.pluginloader.inspect') as minsp:
                        mcandmod.return_value = {f'module{i}{pluginloader.plugins_suffix}':None for i in range(1, 5)}
                        minsp.getmembers.side_effect = [
                            [[f'classname{i}', mock.MagicMock()]]
                            for i, n in enumerate(mcandmod.return_value)] # return different values at each subsequent call
                        misplug.side_effect = lambda n, cl: 'context' if ('1' in n or '3' in n) else None
                        plugcand = pluginloader.load_candidate_modules(self.plugin_paths)
                        plugmap = pluginloader.load_plugins(plugcand)
                        self.assertEqual({'context'}, set(plugmap.keys()))
                        self.assertEqual(2, len(plugmap['context']))
                        for _, pobj in plugmap['context'].items():
                            pobj.setup.assert_called()

    def test_init_tolerates_failing_plugins(self):
        with mock.patch('tattler.server.pluginloader.plugin_category') as misplug:
            with mock.patch('tattler.server.pluginloader.inspect') as minsp:
                pname = f'module1{pluginloader.plugins_suffix}'
                mcandmod = {pname:None}
                mockpluginclass = mock.MagicMock()
                mockpluginclass().setup.side_effect = RuntimeError
                misplug.return_value = 'context'
                minsp.getmembers.return_value = [['foo', mockpluginclass]]
                plugmap = pluginloader.load_plugins(mcandmod)
                mockpluginclass().setup.assert_called()
                self.assertEqual(0, len(plugmap))

    def test_process_context_runs_all_enabled_plugins(self):
        """All enabled context plugins are executed when processing"""
        def addctx(ctx):
            return ctx | {f'{random.randint(1, 10000)}': random.randint(1, 10000)}
        with mock.patch('tattler.server.pluginloader.loaded_plugins') as mplugs:
            mocks = []
            for enab in [True, False, True, False]:
                m = mock.MagicMock()
                m.processing_required.return_value = enab
                if enab:
                    m.process.side_effect = addctx
                mocks.append(m)
            mplugs.get.side_effect = lambda x, y=None: {
                'addressbook': {},
                'context': {f'foo{i}': m for i, m in enumerate(mocks)},
            }.get(x, y)
            have_ctx = pluginloader.process_context({'a': 10, 'x': 20})
            for m in mocks:
                m.processing_required.assert_called()
                if m.processing_required.return_value:
                    m.process.assert_called()
                else:
                    m.process.assert_not_called()
            self.assertEqual(4, len(have_ctx))

    def test_process_context_tolerates_failing_plugins(self):
        """Context plugins that raise exception do not prevent subsequent plugins from running"""
        with mock.patch('tattler.server.pluginloader.loaded_plugins') as mplugs:
            mocks = [mock.MagicMock() for i in range(1, 3)]
            mocks[0].processing_required.side_effect = RuntimeError
            mocks[1].processing_required.return_value = True
            mocks[1].process.side_effect = RuntimeError
            mplugs.get.side_effect = lambda x, y=None: {
                'addressbook': {},
                'context': {f'foo{i}': m for i, m in enumerate(mocks)},
            }.get(x, y)
            pluginloader.process_context({})
            for m in mocks:
                m.processing_required.assert_called()
                if m.processing_required.side_effect:
                    m.process.assert_not_called()
                else:
                    m.process.assert_called()

    def test_lookup_contacts_stops_at_first_successful(self):
        """Addressbook lookups stop at first successful plugin"""
        with mock.patch('tattler.server.pluginloader.loaded_plugins') as mplugs:
            mocks = []
            for enab in [False, False, False, True, True]:
                m = mock.MagicMock()
                m.recipient_exists.return_value = enab
                if m.recipient_exists.return_value:
                    m.attributes.return_value = get_addressbook_retval()
                mocks.append(m)
            mplugs.get.side_effect = lambda x, y=None: {
                'addressbook': {f'addrbookplugin{i}': m for i, m in enumerate(mocks)},
                'context': {},
            }.get(x, y)
            have_contacts = pluginloader.lookup_contacts('recx')
            for m in mocks[:4]:
                m.recipient_exists.assert_called()
                if m.recipient_exists.return_value:
                    m.attributes.assert_called_with('recx')
                else:
                    m.attributes.assert_not_called()
            mocks[4].recipient_exists.assert_not_called()
            mocks[4].attributes.assert_not_called()
            self.assertEqual(4, len(have_contacts))

    def test_lookup_contacts_tolerates_failing_plugins(self):
        """An addressbook plugin raising exceptions does not prevent subsequent ones from running"""
        with mock.patch('tattler.server.pluginloader.loaded_plugins') as mplugs:
            mocks = [mock.MagicMock() for i in range(3)]
            mocks[0].recipient_exists.side_effect = RuntimeError
            mocks[1].recipient_exists.return_value = True
            mocks[1].attributes.side_effect = RuntimeError
            mocks[2].recipient_exists.return_value = True
            mocks[2].attributes.return_value = get_addressbook_retval()
            mplugs.get.side_effect = lambda x, y=None: {
                'addressbook': {f'addrbookplugin{i}': m for i, m in enumerate(mocks)},
                'context': {},
            }.get(x, y)
            have_contacts = pluginloader.lookup_contacts('recx')
            mocks[0].recipient_exists.assert_called()
            mocks[0].attributes.assert_not_called()
            mocks[1].recipient_exists.assert_called()
            mocks[1].attributes.assert_called()
            mocks[2].recipient_exists.assert_called()
            mocks[2].attributes.assert_called()
            self.assertEqual(have_contacts, mocks[2].attributes.return_value)


if __name__ == '__main__':
    unittest.main()