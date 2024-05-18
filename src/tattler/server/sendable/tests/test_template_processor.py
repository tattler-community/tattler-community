"""Test cases for the base template processor"""


import unittest
from pathlib import Path

from tattler.server.sendable.template_processor import TemplateProcessor

class TemplateProcessorTest(unittest.TestCase):
    """Test cases for the base template processor class"""

    def test_expand_event_template_error(self):
        """Expanding template raises KeyError upon undefined variable in event template"""
        tpath = Path(__file__).parent / 'fixtures' / 'templates_with_base'
        content = tpath.joinpath('event2_error', 'sms', 'body.txt').read_text(encoding='utf-8')
        base_content = tpath.joinpath('_base', 'sms', 'body.txt').read_text(encoding='utf-8')
        t = TemplateProcessor(content=content, base_content=base_content)
        with self.assertRaises(KeyError) as err:
            t.expand()
        self.assertIn('Error expanding template', str(err.exception))

    def test_expand_base_template_error(self):
        """Expanding template raises KeyError upon undefined variable in base template"""
        tpath = Path(__file__).parent.joinpath('fixtures', 'templates_with_base_error', 'event1', 'sms', 'body.txt')
        content = Path(tpath).read_text(encoding='utf-8')
        base_content = Path('fixtures/templates_with_base_error/_base/sms/body.txt').read_text(encoding='utf-8')
        t = TemplateProcessor(content=content, base_content=base_content)
        with self.assertRaises(KeyError) as err:
            t.expand()
        self.assertIn('Error expanding base template', str(err.exception))


if __name__ == '__main__':
    unittest.main()
