"""Serialization logic to transport client objects faithfully over JSON to server"""

from datetime import datetime, date

from collections.abc import Mapping, Set

import json

class JSONComplEncoder(json.JSONEncoder):
    """JSON encoder supporting sets, dates and datetimes"""
    def default(self, obj):
        if isinstance(obj, datetime) or isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Mapping):    # e.g. SQLAlchemy Row._mapping
            return dict(obj)
        if isinstance(obj, Set):
            return sorted(obj)

def serialize_json(dictionary):
    """Serialize data into JSON supporting objects otherwise not json-serializable"""
    return json.dumps(dictionary, cls=JSONComplEncoder).encode()
