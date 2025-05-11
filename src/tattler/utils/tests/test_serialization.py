"""Tests for tattler's serialization logic"""

import json
import unittest
from datetime import datetime, date, time, timedelta, timezone
from typing import Any
from types import SimpleNamespace
from collections.abc import Mapping

from tattler.utils import serialization


class SerializationTest(unittest.TestCase):
    """Tests for serialization logic"""

    def test_serialize_objects_timestamp(self):
        """serialize_json() gracefully supports timestamps"""
        now = datetime.now(tz=timezone.utc)
        js = serialization.serialize_json({'foo': now})
        self.assertIsInstance(js, bytes)
        jsdec = js.decode(encoding="utf-8")
        self.assertIn('"foo":', jsdec)
        self.assertIn(now.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'), jsdec)

    def test_serialize_maps(self):
        """serialize_json() gracefully supports maps"""
        jsdec = serialization.serialize_json({'bar': {'1': 1, '2': 2}}).decode(encoding='utf-8')
        self.assertIn('"bar":', jsdec)
        self.assertIn('"1":', jsdec)
    
    def test_serialize_sets(self):
        """serialize_json() gracefully supports sets, converts them as sorted lists"""
        jsdec = serialization.serialize_json({'set1': {3, 1, 2}}).decode(encoding='utf-8')
        self.assertIn('"set1":', jsdec)
        self.assertIn('[1, 2, 3]', jsdec)

    def test_serialize_mapping_objects(self):
        """serialize_json() gracefully supports sets, converts them as sorted lists"""
        class MyMappingNonDict(Mapping):
            """A mapping-like, non-dict object"""
            def __getitem__(self, k, v=None):
                return 3
            def __len__(self):      # pragma: no cover
                return 1
            def __iter__(self):
                yield 'a'
        # mapt = Counter(a=4, b=5)
        jsdec = serialization.serialize_json({'map1': MyMappingNonDict()}).decode(encoding='utf-8')
        self.assertIn('"map1":', jsdec)
        self.assertIn('{"a": 3}', jsdec)

    def test_serialize_objects(self):
        """Serializing objects only returns properties and omits methods"""
        badobj = SimpleNamespace(x=10, foo=lambda x: 10)
        res = serialization.serialize_json(badobj)
        dec = json.loads(res)
        self.assertIsInstance(dec, dict)
        self.assertIn('x', dec)
        self.assertEqual(dec['x'], 10)
        self.assertNotIn('foo', dec)

    def test_serialize_function_fails(self):
        """Serializing a function raises TypeError"""
        with self.assertRaises(TypeError) as err:
            serialization.serialize_json(lambda x: 10)
        self.assertIn('function', str(err.exception))

    def test_serialize_django_orm_flat(self):
        """Serialize a flat model object from Django ORM"""
        # reproduce a django object without drawing in Django as a dependency
        tnow = datetime.now().replace(microsecond=0)
        dur = timedelta(days=2, hours=1, minutes=5, seconds=12, microseconds=456)
        djorm = SimpleNamespace(DoesNotExist=None,
                                clean=None,
                                full_clean=None,
                                _meta=None,
                                _hiddenkey={ 'foo': 'bar', 'x': 1 },
                                tstamp=tnow,
                                tdate=tnow.date(),
                                ttime = tnow.time(),
                                jsonf=[1, 2, 3],
                                intf=123,
                                charf='myfield',
                                duratf=dur,
                                emailf='asd@foo.com',
                                floatf=10/3
                                )
        jsdec = serialization.serialize_json(djorm)
        dec: dict[str, Any] = json.loads(jsdec)
        self.assertIsInstance(dec, dict)
        for unwanted in ['_meta', '_hiddenkey']:
            self.assertNotIn(unwanted, dec, msg=f"Unwanted key '{unwanted}'")
        want = {
            'tstamp':   '^tattler^datetime^' + tnow.isoformat(),
            'tdate':    '^tattler^date^' + tnow.date().isoformat(),
            'ttime':    '^tattler^time^' + tnow.time().isoformat(),
            'duratf':   '^tattler^timedelta^P2D3912S456u',
            'jsonf':    [1, 2, 3],
            'intf':     123,
            'charf':    'myfield',
            'emailf':   'asd@foo.com',
            'floatf':   10/3
        }
        self.assertGreaterEqual(dec.items(), want.items())
    
    def test_serialize_djang_orm_foreignkey(self):
        """Serialize a model object from Django ORM with ForeignKeys in it"""
        djorm = SimpleNamespace(DoesNotExist=None,
                                clean=None,
                                full_clean=None,
                                _meta=None,
                                plainstr='plain string',
                                foo_id='my_id',
                                foo={
                                    'intf': 10,
                                    'strf': 'hello',
                                    'deeper_key_id': 'deepid',
                                    'deeper_key': {
                                        'floatf': 3/2,
                                        'strf': 'world',
                                    }
                                },
                                bar_id='1234',
                                bar={
                                    'emailf': 'asd@foo.com',
                                })
        jsdec = serialization.serialize_json(djorm)
        dec = json.loads(jsdec)
        self.assertIsInstance(dec, dict)
        # foo
        self.assertIn('foo_id', dec)
        self.assertEqual(dec['foo_id'], 'my_id')
        self.assertIn('foo', dec)
        self.assertIsInstance(dec['foo'], dict)
        self.assertIn('deeper_key_id', dec['foo'])
        self.assertEqual(dec['foo']['deeper_key_id'], 'deepid')
        self.assertIsInstance(dec['foo']['deeper_key'], dict)
        self.assertEqual(dec['foo']['deeper_key'], {'floatf': 3/2, 'strf': 'world'})
        # bar
        self.assertIn('bar_id', dec)
        self.assertEqual(dec['bar_id'], '1234')
        self.assertIn('bar', dec)
        self.assertIsInstance(dec['bar'], dict)
        self.assertEqual(dec['bar'], {'emailf': 'asd@foo.com'})


class DeserializationTest(unittest.TestCase):
    """Unit tests for type conversion and serialization logic"""

    # serialization_prefixes:
    #     timedelta    '^tattler^timedelta^P'
    #     time         '^tattler^time^'
    #     date         '^tattler^date^'
    #     datetime     '^tattler^datetime^'

    def test_decode_django_json_supports_list(self):
        """decode_django_json() can take a list and return converted items"""
        res = serialization.decode_django_json(['^tattler^date^2010-01-02', '^tattler^datetime^2022-05-26T11:26:20.246090'])
        self.assertEqual([date(2010, 1, 2), datetime(2022, 5, 26, 11, 26, 20, 246090)], res)

    def test_decode_django_json_supports_dict(self):
        """decode_django_json() can take a dict and return converted values"""
        res = serialization.decode_django_json({
            "1": '^tattler^date^2010-01-02',
            "2": '^tattler^datetime^2022-05-26T11:26:20.246090',
            "3": "^tattler^time^11:26:20.246090",
            "4": "^tattler^time^11"})
        want_items = {
            "1": date(2010, 1, 2),
            "2": datetime(2022, 5, 26, 11, 26, 20, 246090),
            "3": time(11, 26, 20, 246090),
            "4": time(11, 0, 0, 0)
            }
        for k, have in res.items():
            want = want_items.get(k, None)
            self.assertIsNotNone(want, msg=f"Item {k}: {have}")
            self.assertEqual(want, have, msg=f"Item {k}: {have}")

    def test_decode_timedelta_survives_invalid_values(self):
        """decode_timedelta() raises ValueError when being passed invalid values"""
        for badv in ['', '^tattler^',
                     '^tattler^timedelta^',
                     '^tattler^timedelta^PSu', '^tattler^timedelta^-0P1D2S3u']:
            with self.assertRaises(ValueError):
                serialization.decode_timedelta(badv)

    def test_decode_django_json_transparency(self):
        """decode_django_json() returns initial object if it cannot be converted to a time"""
        res = serialization.decode_django_json(['^tattler^date^2010-01-02', 'foo', list(range(10)), '^tattler^datetime^2022-05-26T11:26:20.246090'])
        want_items = [date(2010, 1, 2), 'foo', list(range(10)), datetime(2022, 5, 26, 11, 26, 20, 246090)]
        for i, items in enumerate(zip(res, want_items)):
            have, want = items
            self.assertEqual(have, want, msg=f"Mismatch in item #{i}")

    def test_decode_json_duration(self):
        """decode_django_json() returns initial timedelta after receiving respective string"""
        self.assertEqual(serialization.decode_django_json('^tattler^timedelta^P123D128748S3u'), timedelta(days=123, seconds=128748, microseconds=3))

    def test_decode_json_duration_fail(self):
        """decode_django_json() raises ValueError after receiving invalid string"""
        with self.assertRaises(ValueError):
            self.assertEqual(serialization.decode_django_json('^tattler^timedelta^P-123D128748S3u'), timedelta(days=123, seconds=128748, microseconds=3))

    def test_deserialize_json(self):
        """deserialize_json() returns symmetric of serialize_json()"""
        inobj = {
            'dt': datetime.now(),
            'td': timedelta(seconds=12),
            'bar': {
                'a': 1,
                'b': list(range(10)),
            }
        }
        serbytes = serialization.serialize_json(inobj)
        self.assertEqual(inobj, serialization.deserialize_json(serbytes))
