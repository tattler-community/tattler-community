"""Test client utilities"""

import unittest
import unittest.mock
from datetime import datetime, timezone
import random
from collections import Counter

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
        mapt = Counter(a=4, b=5)
        jsdec = serialize_json({'map1': mapt}).decode(encoding='utf-8')
        self.assertIn('"map1":', jsdec)
        self.assertIn('{"a": 4, "b": 5}', jsdec)
