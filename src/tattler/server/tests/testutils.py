import os

def get_template_dir():
    if os.getenv('TATTLER_TEMPLATE_BASE'):
        return os.getenv('TATTLER_TEMPLATE_BASE')
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'fixtures', 'templates_dir')

