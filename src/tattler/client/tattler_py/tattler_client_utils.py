"""Utilities for tattler client"""

import os
import uuid
from typing import Optional, Tuple

DEFAULT_ADDRESS = '127.0.0.1'
DEFAULT_PORT = 11503

def getenv(name: str, default: Optional[str]=None) -> Optional[str]:
    """Get variable from environment -- allowing mocking"""
    return os.getenv(name, default)

def mk_correlation_id(prefix: Optional[str]='tattler') -> str:
    """Generate a random correlation ID, for sessions where none has been pre-provided.
    
    :param prefix:      Optional string to prepend to the returned random ID ('prefix:id'); set to None for no string ('prefix').

    :return:            Random ID suitable for correlation logging, potentially prefixed with given prefix."""
    if prefix:
        return f'{prefix}:{uuid.uuid4()}'
    return str(uuid.uuid4())

def get_endpoint_config(envvar_name: str) -> Tuple[str, int]:
    """Retrieve the configuration for the server endpoint from an environment variable.
    
    :param envvar_name:     Name of environment variable to seek configuration in.
    :return:                The pair (address, port) of the server to contact.
    """
    endpoint_str = getenv(envvar_name)
    if endpoint_str is None:
        return DEFAULT_ADDRESS, DEFAULT_PORT
    endpoint_str = endpoint_str.strip()
    try:
        srv, port = endpoint_str.rsplit(':', 1)
        return srv, int(port)
    except ValueError as err:
        raise ValueError(f"Endpoint '{endpoint_str}' fails to provide valid port value, want addr:port") from err
