import os
import uuid
from typing import Optional

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
