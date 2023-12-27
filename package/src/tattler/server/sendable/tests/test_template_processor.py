import unittest
from pathlib import Path

from tattler.server.sendable.template_processor import TemplateProcessor

class TemplateProcessorTest(unittest.TestCase):
    def test_expand_event_template_error(self):
        content = Path('fixtures/templates_with_base/event2_error/sms').read_text(encoding='utf-8')
        base_content = Path('fixtures/templates_with_base/_base/sms').read_text(encoding='utf-8')
        t = TemplateProcessor(content=content, base_content=base_content)
        with self.assertRaises(TypeError) as err:
            t.expand()
        self.assertIn('Error expanding template', str(err.exception))

    def test_expand_base_template_error(self):
        content = Path('fixtures/templates_with_base_error/event1/sms').read_text(encoding='utf-8')
        base_content = Path('fixtures/templates_with_base_error/_base/sms').read_text(encoding='utf-8')
        t = TemplateProcessor(content=content, base_content=base_content)
        with self.assertRaises(TypeError) as err:
            t.expand()
        self.assertIn('Error expanding base template', str(err.exception))
