"""Tests for template utils"""

from pathlib import Path

import testutils_templates

contacts = {
    'email': 'xyz@test321.com',
    'sms': '+19876543210'
}

testutils_templates.templates_base = Path(__file__).parent.parent / 'templates'

testutils_templates.event_contexts = {
    '_base': {
        'notification_id': testutils_templates.mk_random_string()
    }
}

# don't create symlink for existing base
testutils_templates.target_base_path = None

class TattlerTemplateTest(testutils_templates.TemplateTest):
    """Wrapper to execute template tests"""
