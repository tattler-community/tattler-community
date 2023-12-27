from datetime import datetime, date

import json

class JSONComplEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime) or isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, set):
            return sorted(obj)

def serialize_json(dictionary):
    return json.dumps(dictionary, cls=JSONComplEncoder).encode('utf-8')

def deserialize_json(data):
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    return json.loads(data)