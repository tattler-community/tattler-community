"""Tests for templatemgr"""

import unittest
from unittest import mock
import random
from pathlib import Path

from tattler.server.templatemgr import TemplateMgr, get_scopes

class TemplateManagerTest(unittest.TestCase):
    """Tests for TemplateManager"""

    template_scopes_path = Path(__file__).parent / 'fixtures' / 'templates_dir'
    validation_templates_path = Path(__file__).parent / 'fixtures' / 'templates_dir_validation'
    good_templates_path = template_scopes_path / 'testcontext'
    bad_templates_path = Path().joinpath('foo', 'basd', f'aslkfdj.{random.randint(100000, 99999999)}')

    def test_reject_bad_basedir(self):
        with self.assertRaises(FileNotFoundError, msg="TemplateMgr failed to raise ValueError upon bad folder") as e:
            tm = TemplateMgr(self.bad_templates_path)

    def test_accept_good_basedir(self):
        tm = TemplateMgr(self.good_templates_path)

    def test_available_scopes(self):
        tm = TemplateMgr(self.good_templates_path)
        have_scopes = get_scopes(self.template_scopes_path)
        self.assertNotIn('_base', have_scopes)
        self.assertEqual({'jinja', 'testcontext'}, set(have_scopes))

    def test_available_scopes_inexistent_dir(self):
        """get_scopes() for inexistent dir returns empty"""
        have_scopes = get_scopes(self.bad_templates_path)
        self.assertIsInstance(have_scopes, set)
        self.assertFalse(have_scopes)

    def test_available_events_includes_all_valid(self):
        tm = TemplateMgr(self.good_templates_path)
        have = tm.available_events()
        want = {'valid_event'}
        self.assertGreaterEqual(have, want)

    def test_available_events_excludes_invalid(self):
        tm = TemplateMgr(self.good_templates_path)
        have = tm.available_events()
        unwant = set(['invalid_event'])
        self.assertEqual(unwant-have, unwant)
    
    def test_available_events_including_hidden(self):
        tm = TemplateMgr(self.good_templates_path)
        self.assertGreater(tm.available_events(with_hidden=True), tm.available_events(with_hidden=False))
        self.assertEqual({'_base', '_other_hidden_event'}, tm.available_events(with_hidden=True) - tm.available_events(with_hidden=False))
    
    def test_multilingualism_succeeds_empty(self):
        """available_languages() can be called safely but always returns empty set"""
        tm = TemplateMgr(self.good_templates_path)
        self.assertEqual(set(), set(tm.available_languages('valid_event', 'sms')))

    def test_validate_templates_valid(self):
        """validate_templates() on template manager succeeds on valid dirs."""
        with mock.patch('tattler.server.templatemgr.TemplateMgr'):
            tm = TemplateMgr(self.validation_templates_path / 'scope_good')
            tm.validate_templates()

    def test_validate_templates_invalid(self):
        """validate_templates() on template manager raises on invalid dirs."""
        with mock.patch('tattler.server.templatemgr.TemplateMgr'):
            tm = TemplateMgr(self.validation_templates_path / 'scope_bad')
            with self.assertRaises(ValueError, msg="validate_templates() does not raise upon templates dir with malformed events."):
                tm.validate_templates()

    def test_validate_configuration_triggers_required_vectors(self):
        """validate_configuration() on template manager triggers required vectors"""
        ret_vecs = {
            'sms': mock.MagicMock(),
            'email': mock.MagicMock(),
        }
        with mock.patch('tattler.server.templatemgr.Sendable') as msnd:
            with mock.patch('tattler.server.templatemgr.get_vector_class') as mgetvcl:
                with mock.patch('tattler.server.templatemgr.TemplateMgr.available_vectors') as mavvec:
                    mavvec.return_value = {'sms'}
                    mgetvcl.side_effect = ret_vecs.get
                    # sms
                    tm = TemplateMgr(self.validation_templates_path / 'scope_good')
                    tm.validate_configuration()
                    msnd.validate_configuration.assert_called()
                    self.assertEqual(1, ret_vecs['sms'].validate_configuration.call_count)
                    self.assertEqual(0, ret_vecs['email'].validate_configuration.call_count)
                    msnd.reset_mock()
                    mavvec.return_value = {'sms'}
                    for m in ret_vecs.values():
                        m.reset_mock()
                    # email and sms
                    mavvec.return_value = {'sms', 'email'}
                    tm = TemplateMgr(self.validation_templates_path / 'scope_bad')
                    tm.validate_configuration()
                    msnd.validate_configuration.assert_called()
                    self.assertEqual(1, ret_vecs['sms'].validate_configuration.call_count)
                    self.assertEqual(1, ret_vecs['email'].validate_configuration.call_count)

if __name__ == '__main__':
    unittest.main()
