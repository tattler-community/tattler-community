import os
from contextlib import contextmanager

data_recipients = {
    'email': ['support@test123.com'],
    'sms': ['+11234567898', '00417689876']
}
template_base = os.path.join('fixtures', 'templates')


def get_lines_without_comments(blacklist_path):
    with open(blacklist_path) as f:
        return set([line.strip() for line in f if not line.startswith('#')])

@contextmanager
def temp_envvar(env_varname, value):
    orig_envv = os.getenv(env_varname, None)
    os.environ[env_varname] = value
    try:
        yield
    finally:
        if orig_envv is None:
            del os.environ[env_varname]
        else:
            os.environ[env_varname] = orig_envv

