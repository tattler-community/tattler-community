"""Logic to serialize and deserialize objects between client and server"""

import re
import json
from datetime import timedelta, datetime, date, time
from typing import Any

from collections.abc import Mapping, Set

def encode_timedelta(value: timedelta) -> str:
    """Encode a timedelta into a string which is unlikely to occur otherwise.
    
    :return:        String representation for wire.
    """
    return f'P{value.days}D{value.seconds}S{value.microseconds}u'


def decode_timedelta(value: str) -> timedelta:
    """Decode a string into a timedelta.
    
    :raises ValueError:     The format or semantic of the given string does not allow decoding.

    :return:        Timedelta representation of the duration of the given string.
    """
    res = re.match(r'P(?P<days>[0-9]+)D(?P<secs>[0-9]+)S(?P<micros>[0-9]+)u', value)
    if res is None:
        raise ValueError('Not formatted as a valid tattler duration (invalid fields)')
    days, seconds, micros = [int(res.group(p)) for p in ['days', 'secs', 'micros']]
    return timedelta(days=days, seconds=seconds, microseconds=micros)


class DjangoJSONEncoder(json.JSONEncoder):
    """JSON encoder supporting sets, dates and datetimes"""
    
    def default(self, o):
        """Encode individual object based on its type, or return parent to raise error."""
        if isinstance(o, datetime):
            return '^tattler^datetime^' + o.isoformat()
        if isinstance(o, date):
            return '^tattler^date^' + o.isoformat()
        if isinstance(o, time):
            return '^tattler^time^' + o.isoformat()
        if isinstance(o, timedelta):
            return '^tattler^timedelta^' + encode_timedelta(o)
        if isinstance(o, Mapping):    # e.g. SQLAlchemy Row._mapping
            return dict(o) if not isinstance(o, dict) else o
        if isinstance(o, Set):
            return sorted(o)
        if isinstance(o, object) and getattr(o, '__call__', None) is None:
            props = {k: v for k, v in o.__dict__.items() if getattr(v, '__call__', None) is None and not k.startswith('_')}
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

def decode_django_json(obj: Any) -> Any:
    """Return most fitting python representation of object out of a JSON serialization.

    For example, this replaces a time string with a :class:`datetime.time` object.

    Nota bene: tattler relies on an internal protocol to extend JSON with annotations
    on the original format of the object encoded. For example:

    - :class:`datetime.datetime` objects are serialized as ISO8601 datetime strings, prefixed with ``^tattler^datetime^``.

    - :class:`datetime.date` objects are serialized as ISO8601 date strings, prefixed with ``^tattler^date^``.
    
    - :class:`datetime.time` objects are serialized as ISO8601 time strings, prefixed with ``^tattler^time^``.
    
    - :class:`datetime.timedelta` objects are serialized as ISO8601 duration strings, prefixed with ``^tattler^timedelta^``.

    This is a 'object_hook' function for :mod:`json` decoding. Use e.g. as:
    ``json.loads(value, object_hook=decode_django_json)``.
    
    :param obj:     The object to serialize.
    :return:        Either the initial object, or a refined version of it.
    """
    tattler_deserialization_prefixes = {
        '^tattler^timedelta^':     decode_timedelta,
        '^tattler^time^':          time.fromisoformat,
        '^tattler^date^':          date.fromisoformat,
        '^tattler^datetime^':      datetime.fromisoformat,
    }
    assert all(p.startswith('^tattler^') for p in tattler_deserialization_prefixes)
    if isinstance(obj, dict):
        return {k:decode_django_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [decode_django_json(v) for v in obj]
    if isinstance(obj, str) and obj.startswith('^tattler^'):
        for special_prefix, decoder_f in tattler_deserialization_prefixes.items():
            if obj.startswith(special_prefix):
                return decoder_f(obj[len(special_prefix):])
    return obj


def serialize_json(dict_like_data: Mapping[str: Any]) -> bytes:
    """Serialize data into JSON supporting objects otherwise not json-serializable.
    
    :param dict_like_date:  A mapping-like object that can be JSON serialized.
    
    :return:            The byte string holding a serialized version of the content of the object."""
    return json.dumps(dict_like_data, cls=DjangoJSONEncoder).encode('utf-8')


def deserialize_json(content: bytes) -> Mapping[str: Any]:
    """De-serialize a byte string into a complex python object.
    
    :param content: The byte string holding the serialized version of the object.
    
    :return:        A python mapping-like object with key:value pairs and possible nested objects."""
    return json.loads(content.decode(encoding='utf-8'), object_hook=decode_django_json)
