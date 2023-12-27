import os
import unittest
from datetime import datetime, timedelta

from testutils import get_template_dir

from tattler.server.sendable import EmailSendable
from tattler.server.templateprocessor_jinja import JinjaTemplateProcessor

class JinjaTemplateProcessorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.template_scopes_path = get_template_dir()
        self.good_templates_path = os.path.join(self.template_scopes_path, 'jinja')

    def test_expansion_with_base(self):
        # Plain
        es = EmailSendable('jinja_event', [], template_processor=JinjaTemplateProcessor, template_base=self.good_templates_path)
        # plain text
        txtcontent = es._get_content_part('body_plain', {})
        self.assertIn("Text base", txtcontent)
        self.assertIn("new text", txtcontent)
        self.assertNotIn("replace text", txtcontent)
        # HTML
        htmlcontent = es._get_content_part('body_html', {})
        self.assertIn("HTML base", htmlcontent)
        self.assertIn("new HTML", htmlcontent)
        self.assertNotIn("replace HTML", htmlcontent)

    def test_expansion_converts_to_native(self):
        context = {
            'time1': '2021-09-29T17:03:36Z',
            'time2': '2021-09-29T17:23:36Z',
            'ival1': 1,
            'ival2': 2,
            'fval1': 5/3,
            'fval2': 10/3,
            'sval1': 'one',
            'sval2': 'two',
        }
        txtcontent = open(os.path.join(self.good_templates_path, 'jinja_variable_expressions', 'sms')).read()
        tpj = JinjaTemplateProcessor(content=txtcontent)
        string_context = {k:str(v) for k, v in context.items()}
        self.assertEqual(tpj.expand(string_context), '0:20:00 3 0.5 onetwo')
    
    def test_humanize(self):
        now = datetime(2021, 9, 29, 18, 28, 27, 791489)
        context = {
            'vdelta': timedelta(seconds=8763),
            'vtime': now,
            'vdate': now.date(),
            'vint': 12345591313,
        }
        content = open(os.path.join(self.good_templates_path, 'jinja_humanize', 'sms')).read()
        tpj = JinjaTemplateProcessor(content=content)
        result = tpj.expand(context)
        self.assertIn('#2 hours', result)
        self.assertIn(' ago', result)
        self.assertIn('#12.3 billion', result)
        self.assertIn('2021', result)

if __name__ == "__main__":
    unittest.main()