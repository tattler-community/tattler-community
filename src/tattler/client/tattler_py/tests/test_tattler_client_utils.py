"""Test client utilities"""

import json
import unittest
import unittest.mock
from datetime import datetime, timezone, timedelta
import os
import random
from types import SimpleNamespace
from collections.abc import Mapping

from tattler.client.tattler_py import tattler_client_utils
from tattler.client.tattler_py.serialization import serialize_json

def get_random_ip4():
    """Generate a random IPv4 address for testing"""
    return '.'.join([str(random.randint(0, 255)) for i in range(4)])

def get_random_ip6():
    """Generate a random IPv6 address for testing"""
    def ip6_part(n_fields=8):
        return ':'.join([f"{random.randint(0, 255):x}" for i in range(n_fields)])
    # full or shortened?
    if random.getrandbits(1):
        # full
        return ip6_part(8)
    # shortened -> must shortcut '::'. Where?
    shortcut_pos = random.randint(1, 6)
    return ip6_part(shortcut_pos) + '::' + ip6_part(7-shortcut_pos)


class TattlerClientUtilsTest(unittest.TestCase):
    """Tests for client utils"""

    def test_mk_correlation_id_sane_output(self):
        """mk_correlation_id() returns strings with requested properties"""
        self.assertIsInstance(tattler_client_utils.mk_correlation_id(), str)
        self.assertTrue(tattler_client_utils.mk_correlation_id())
        self.assertGreaterEqual(len(tattler_client_utils.mk_correlation_id()), 6)
        self.assertTrue(tattler_client_utils.mk_correlation_id(prefix='foo').startswith('foo'))
        self.assertTrue(tattler_client_utils.mk_correlation_id(prefix='bar').startswith('bar'))
        many_outputs = {tattler_client_utils.mk_correlation_id() for i in range(1000)}
        self.assertEqual(len(many_outputs), 1000)

    def test_get_endpoint_config_noconf(self):
        """get_endpoint_config() returns default endpoint if no config given"""
        with unittest.mock.patch('tattler.client.tattler_py.tattler_client_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda k,v=None: {'TATTLER_SERVER_ADDRESS': None}.get(k, os.getenv(k, v))
            res = tattler_client_utils.get_endpoint_config('TATTLER_SERVER_ADDRESS')
            self.assertIsNotNone(res)
            self.assertIsInstance(res, tuple)
            self.assertEqual(2, len(res))
            self.assertIsInstance(res[0], str)
            self.assertIsInstance(res[1], int)
            self.assertEqual(res, (tattler_client_utils.DEFAULT_ADDRESS, tattler_client_utils.DEFAULT_PORT))

    def test_get_endpoint_config_honors_envvar(self):
        """get_endpoint_config() honors the name of the envvar to look up"""
        with unittest.mock.patch('tattler.client.tattler_py.tattler_client_utils.getenv') as mgetenv:
            for _ in range(5):
                varname = f'TATTLER_{random.randint(1000, 100000)}'
                srv = f'{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}'
                port = random.randint(1, 65535)
                mgetenv.side_effect = lambda k,v=None: {varname: f'{srv}:{port}'}.get(k, os.getenv(k, v))
                res = tattler_client_utils.get_endpoint_config(varname)
                self.assertIsNotNone(res)
                self.assertEqual(res, (srv, port), msg=f"get_endpoint_config() did not honor envvar name '{varname}'")
                mgetenv.assert_called_once_with(varname)
                mgetenv.reset_mock()

    def test_get_endpoint_config_raises_malformatted(self):
        """get_endpoint_config() supports various format"""
        with unittest.mock.patch('tattler.client.tattler_py.tattler_client_utils.getenv') as mgetenv:
            for conf in ['asd', ':asd', ':123asd', '1.2.3.4:', '2a00:1450:400a:801::200e']:
                mgetenv.side_effect = lambda k,v=None: {'TATTLER_SERVER_ADDRESS': conf}.get(k, os.getenv(k, v))
                with self.assertRaises(ValueError, msg=f"With '{conf}'") as err:
                    tattler_client_utils.get_endpoint_config('TATTLER_SERVER_ADDRESS')
                self.assertIn('provide valid port value', str(err.exception), msg=f"With '{conf}'")


class TestSerialization(unittest.TestCase):
    """Tests for serialization logic"""

    def test_serialize_objects_timestamp(self):
        """serialize_json() gracefully supports timestamps"""
        now = datetime.now(tz=timezone.utc)
        js = serialize_json({'foo': now})
        self.assertIsInstance(js, bytes)
        jsdec = js.decode(encoding="utf-8")
        self.assertIn('"foo":', jsdec)
        self.assertIn(now.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'), jsdec)

    def test_serialize_maps(self):
        """serialize_json() gracefully supports maps"""
        jsdec = serialize_json({'bar': {'1': 1, '2': 2}}).decode(encoding='utf-8')
        self.assertIn('"bar":', jsdec)
        self.assertIn('"1":', jsdec)
    
    def test_serialize_sets(self):
        """serialize_json() gracefully supports sets, converts them as sorted lists"""
        jsdec = serialize_json({'set1': {3, 1, 2}}).decode(encoding='utf-8')
        self.assertIn('"set1":', jsdec)
        self.assertIn('[1, 2, 3]', jsdec)

    def test_serialize_mapping_objects(self):
        """serialize_json() gracefully supports sets, converts them as sorted lists"""
        class MyMappingNonDict(Mapping):
            def __getitem__(k, v=None):
                return 3
            def __len__(self):
                return 1
            def __iter__(self):
                yield 'a'
        # mapt = Counter(a=4, b=5)
        jsdec = serialize_json({'map1': MyMappingNonDict()}).decode(encoding='utf-8')
        self.assertIn('"map1":', jsdec)
        self.assertIn('{"a": 3}', jsdec)

    def test_serialize_objects(self):
        """Serializing objects only returns properties and omits methods"""
        badobj = SimpleNamespace(x=10, foo=lambda x: 10)
        res = serialize_json(badobj)
        dec = json.loads(res)
        self.assertIsInstance(dec, dict)
        self.assertIn('x', dec)
        self.assertEqual(dec['x'], 10)
        self.assertNotIn('foo', dec)

    def test_serialize_function_fails(self):
        """Serializing a function raises TypeError"""
        with self.assertRaises(TypeError) as err:
            serialize_json(lambda x: 10)
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
                                jsonf=[1, 2, 3],
                                intf=123,
                                charf='myfield',
                                duratf=dur,
                                emailf='asd@foo.com',
                                floatf=10/3
                                )
        jsdec = serialize_json(djorm)
        dec = json.loads(jsdec)
        self.assertIsInstance(dec, dict)
        for unwanted in ['_meta', '_hiddenkey']:
            self.assertNotIn(unwanted, dec, msg=f"Unwanted key '{unwanted}'")
        want = {
            'tstamp': tnow.isoformat(),
            'jsonf': [1, 2, 3],
            'intf': 123,
            'charf': 'myfield',
            'duratf': '^tattler^timedelta^P2D3912S456u',
            'emailf': 'asd@foo.com',
            'floatf': 10/3
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
        jsdec = serialize_json(djorm)
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


if __name__ == '__main__':
    unittest.main()         # pragma: no cover
