"""Serialization logic to transport client objects faithfully over JSON to server"""

from datetime import datetime, date, timedelta
import json

from collections.abc import Mapping, Set


TATTLER_TIMEDELTA_PREFIX = '^tattler^timedelta^P'


def encode_timedelta(value: timedelta) -> str:
    """Encode a timedelta into a string which is unlikely to occur otherwise.
    
    :return:        String representation for wire.
    """
    return f'{TATTLER_TIMEDELTA_PREFIX}{value.days}D{value.seconds}S{value.microseconds}u'


class DjangoJSONEncoder(json.JSONEncoder):
    """JSON encoder supporting sets, dates and datetimes"""
    
    def default(self, o):
        """Encode individual object based on its type, or return parent to raise error."""
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, timedelta):
            return encode_timedelta(o)
        if isinstance(o, Mapping):    # e.g. SQLAlchemy Row._mapping
            return dict(o) if not isinstance(o, dict) else o
        if isinstance(o, Set):
            return sorted(o)
        if isinstance(o, object) and getattr(o, '__call__', None) is None:
            props = {k: v for k, v in o.__dict__.items() if getattr(v, '__call__', None) is None}
            if {'DoesNotExist', 'clean', 'full_clean', '__dict__', '_meta'} - set(dir(o)):
                # regular object. Attempt to serialize as key: value
                return props
            # django model object
            dicto = {k:v for k, v in props.items() if not k.startswith('_')}
            reso = self.default(dicto)
            # add deep objects, if any
            for deepfield in [df.rsplit('_', 1)[0] for df in dicto if df.endswith('_id')]:
                deepo = getattr(o, deepfield, None)
                if deepo is not None:
                    reso[deepfield] = deepo
            return reso
        return super().default(o)

def serialize_json(dictionary):
    """Serialize data into JSON supporting objects otherwise not json-serializable"""
    return json.dumps(dictionary, cls=DjangoJSONEncoder).encode()
