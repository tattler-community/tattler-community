from datetime import datetime, date

import json

class JSONComplEncoder(json.JSONEncoder):
    """JSON encoder supporting sets, dates and datetimes"""
    def default(self, obj):
        if isinstance(obj, datetime) or isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, set):
            return sorted(obj)

def serialize_json(dictionary):
    """Serialize data into JSON supporting objects otherwise not json-serializable"""
    return json.dumps(dictionary, cls=JSONComplEncoder).encode()
