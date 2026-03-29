"""Test cases for the base template processor"""


import unittest

from tattler.server.sendable.template_processor import TemplateProcessor

class TemplateProcessorTest(unittest.TestCase):
    """Test cases for the base template processor class"""

    def test_expand_raises_not_implemented(self):
        """TemplateProcessor.expand() raises NotImplementedError"""
        t = TemplateProcessor(content='hello')
        with self.assertRaises(NotImplementedError):
            t.expand()


if __name__ == '__main__':
    unittest.main()
