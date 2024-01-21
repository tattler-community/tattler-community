"""Tests for templatemgr"""

import unittest
import random
from pathlib import Path

from tattler.server.templatemgr import TemplateMgr, get_scopes

class TemplateManagerTest(unittest.TestCase):
    """Tests for TemplateManager"""

    template_scopes_path = Path(__file__).parent / 'fixtures' / 'templates_dir'
    good_templates_path = template_scopes_path / 'testcontext'
    bad_templates_path = Path(f'/foo/basd/aslkfdj.{random.randint(100000, 99999999)}')

    def test_reject_bad_basedir(self):
        with self.assertRaises(ValueError, msg="TemplateMgr failed to raise ValueError upon bad folder") as e:
            tm = TemplateMgr(self.bad_templates_path)

    def test_accept_good_basedir(self):
        tm = TemplateMgr(self.good_templates_path)

    def test_available_scopes(self):
        tm = TemplateMgr(self.good_templates_path)
        have_scopes = get_scopes(self.template_scopes_path)
        self.assertNotIn('_base', have_scopes)
        self.assertEqual({'jinja', 'testcontext'}, set(have_scopes))

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
