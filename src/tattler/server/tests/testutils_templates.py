"""Utilities for unit test files that test templates"""

import unittest
import os
import re
import logging
from typing import Union
from pwd import getpwuid
from pathlib import Path

import string
import random

from tattler.server import sendable

from tattler.server.templatemgr import TemplateMgr
from tattler.server.templateprocessor_jinja import JinjaTemplateProcessor

contacts = {
    'email': 'xyz@buddyns.com',
    'sms': '+19876543210'
}

# set this path to the directory holding all templates (event names)
templates_base = Path('..') / 'templates'

# path to directory holding _base -- if a symlink should be created to it. Set None to disable symlink
mypath = Path(os.path.realpath(os.path.dirname(__file__)))
target_base_path = os.path.realpath(mypath.parent / 'tattler' / 'server' / 'templates' / '_base')

def mk_random_string(length=20):
    """Return a randomly-generated string of the given length with only letters and digits"""
    return ''.join([random.choice(string.ascii_letters + string.digits) for c in range(length)])

corrId = mk_random_string()

# This context is added to every event. It simulates what's automatically added by tattler
base_context = {
    'user_email': contacts['email'],
    'user_sms': contacts['sms'],
    'user_firstname': 'Xyz',
    'user_account_type': 'free',
    'correlation_id': corrId,
    'notification_id': corrId,
    'notification_mode': 'staging',
    'notification_vector': 'email',
    'notification_scope': 'my_scope_name',
    'event_name': 'my_event_name',
}


# Set this dictionary to contain one key for each event name which requires context variables, and the value = dictionary of the context
event_contexts = {
    # 'event_name': {
    #     'var1': 'value1'
    # }
}

def find_template_base(rootpath: Union[str, os.PathLike]) -> os.PathLike:
    seek = '_base'
    for root, dirs, _ in os.walk(rootpath):
        if os.path.islink(root) or any(x in root.split(os.path.sep) for x in {'.git', 'fixtures'}):
            continue
        if seek in dirs:
            return os.path.realpath(os.path.join(root, seek))
    return None

def clear_symlink_to_base_template():
    local_base_path = templates_base / '_base'
    try:
        os.remove(local_base_path)
    except FileNotFoundError:
        pass
    except PermissionError:
        st = os.stat(local_base_path)
        logging.error("Permission error deleting file '%s', owned by '%s'. Ignoring.", local_base_path, getpwuid(st.st_uid).pw_name)

def create_symlink_to_base_template():
    """Create a symlink to a _base template located elsewhere.
    
    @param  target_base_path  [path]  The path of the _base template to link to, or None for default."""
    clear_symlink_to_base_template()
    local_base_path = templates_base / '_base'
    target_base_path = find_template_base(Path(os.path.dirname(__file__)).parent)
    try:
        os.symlink(target_base_path, local_base_path, target_is_directory=True)
    except FileExistsError:
        pass


class TemplateTest(unittest.TestCase):
    def setUp(self) -> None:
        if target_base_path:
            create_symlink_to_base_template()
        self.tman = TemplateMgr(templates_base)
        return super().setUp()
    
    def tearDown(self) -> None:
        if target_base_path:
            clear_symlink_to_base_template()
        return super().tearDown()

    def test_template_base_with_all_variables_succeeds(self):
        for event_name in self.tman.available_events(with_hidden=True):
            ctx = dict(base_context, **event_contexts.get(event_name, {}))
            for vector in self.tman.available_vectors(event_name):
                n = sendable.make_notification(vector, event_name, [contacts[vector]], template_processor=JinjaTemplateProcessor, template_base=templates_base)
                c = n.content(context=ctx)
                for varname, varval in ctx.items():
                    if re.match(r'{{\s*' + varname + r'\s*}}', n.raw_content()):
                        self.assertIn(varval.lower(), c.lower(), msg=f"Value of variable '{varname}'='{varval}' not found in {vector}:{event_name}.")
