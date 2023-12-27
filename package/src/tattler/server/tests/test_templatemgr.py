import unittest
import random
import os

from testutils import get_template_dir

from tattler.server.templatemgr import TemplateMgr, get_scopes

class TemplateManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.template_scopes_path = get_template_dir()
        self.good_templates_path = os.path.join(self.template_scopes_path, 'testcontext')
        self.bad_templates_path = '/foo/basd/aslkfdj.%d' % random.randint(100000, 99999999)
        return super().setUp()

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