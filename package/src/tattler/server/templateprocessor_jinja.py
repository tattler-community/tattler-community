"""Template processor for Jinja format."""

import logging
import os
from datetime import datetime, date, timedelta
from typing import Optional, Mapping, Any

from jinja2 import Environment
from jinja2.environment import Template
from jinja2.loaders import BaseLoader

import humanize

from tattler.server.sendable import TemplateProcessor

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)

class JinjaTemplateProcessor(TemplateProcessor):
    """A template processor for the Jinja2 template language.
    
    Templates look as follows::

        Hi {{ user_firstname }}!

    See http://jinja.palletsprojects.com/ for details on the language.

    This processor supports "base templates".
    """

    def expand(self, context: Optional[Mapping[str, Any]]=None, **kwargs) -> str:
        """Expand the template into the actual content to deliver.
        
        :param context: None or a dictionary of variables and values.
        :type context: dict or None
        :return: Expanded content for sending.
        :rtype: str
        :raises TypeError: if the template could not be expanded.
        """
        context = context or {}
        base_content = kwargs.get('base_content', None) or self.base_content
        full_context = {}
        if 'base_template' in context:
            log.warning("Omitting base template logic because 'base_template' var already provided in context.")
        elif base_content is not None:
            full_context['base_template'] = Template(base_content)
            log.debug("Base template = '%s'...", base_content[:100])
        full_context.update(context)
        full_context = {vname:convert_to_python(vname, vval) for vname, vval in full_context.items()}
        log.debug("Expanding template with context keys = '%s'", sorted(context.keys()))
        e = Environment(loader=BaseLoader())
        e.filters["humanize"] = humanize_jinja
        t = e.from_string(self.content)
        return t.render(full_context)

def humanize_jinja(value, format=None):
    if format is not None:
        fun = getattr(humanize, format, None)
        if fun is None:
            return value
        return fun(value)
    if isinstance(value, timedelta):
        return humanize.naturaldelta(value)
    elif isinstance(value, datetime):
        return humanize.naturaltime(value)
    elif isinstance(value, date):
        return humanize.naturaldate(value)
    return value

def convert_to_python(varname, varvalue):
    if not isinstance(varvalue, str):
        return varvalue
    try:
        return int(varvalue)
    except ValueError:
        pass
    try:
        return float(varvalue)
    except ValueError:
        pass
    try:
        v = varvalue
        if varvalue.endswith('Z') or varvalue.endswith('+'):
            v = varvalue[:-1]
        return datetime.fromisoformat(v)
    except ValueError:
        pass
    return varvalue
