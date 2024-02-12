"""Base processor class based on vanilla python-style string expansion."""

from typing import Mapping, Optional, Any

class TemplateProcessor:
    """A basic template processor based on python string interpolation, suitable for inheriting more complex processors.
    
    This processor expands template strings in python's string interpolation format::

        Hi %(user_firstname)s!

    It supports base template by expanding its content, and passing
    the result into the content as variable "base_content".

    Inherit from this class and override the expand() method
    to create custom template processors.

    Also see JinjaTemplateProcessor .
    """

    def __init__(self, content: str, base_content: Optional[str]=None, **kwargs) -> None:
        """Construct a Template Processor object.
        
        :param str content: The template definition, in backend-specific syntax.
        :param base_content: An optional additional template (in backend-specific syntax) to base 'content' upon.
        :type base_content: str or None"""
        self.content = content
        self.kwargs = kwargs
        self.base_content = base_content

    def expand(self, context: Optional[Mapping[str, Any]]=None, **kwargs) -> str:
        """Expand the template into the actual content to deliver.
        
        :param context: None or a dictionary of variables and values.
        :type context: dict or None
        :return: Expanded content for sending.
        :rtype: str
        :raises TypeError: if the template could not be expanded.
        """
        full_context = context or {}
        if self.base_content:
            try:
                bcontent = self.base_content % full_context
                full_context = {'base_content': bcontent, **full_context}
            except KeyError as err:
                raise KeyError(f"Error expanding base template with base TemplateProcessor. One or more template-required variable were undefined ({err.args[0]})? Original error: '{err}'. Context: {context}") from err            
        try:
            return self.content % full_context
        except KeyError as err:
            raise KeyError(f"Error expanding template with base TemplateProcessor. One or more template-required variable were undefined ({err.args[0]})? Original error: '{err}'. Context: {context}") from err
