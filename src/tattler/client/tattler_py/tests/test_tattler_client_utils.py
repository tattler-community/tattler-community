import unittest
import unittest.mock
import random

from tattler.client.tattler_py import tattler_client_utils

def get_random_ip4():
    return '.'.join([str(random.randint(0, 255)) for i in range(4)])

def get_random_ip6():
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
    def test_mk_correlation_id_sane_output(self):
        self.assertIsInstance(tattler_client_utils.mk_correlation_id(), str)
        self.assertTrue(tattler_client_utils.mk_correlation_id())
        self.assertGreaterEqual(len(tattler_client_utils.mk_correlation_id()), 6)
        self.assertTrue(tattler_client_utils.mk_correlation_id(prefix='foo').startswith('foo'))
        self.assertTrue(tattler_client_utils.mk_correlation_id(prefix='bar').startswith('bar'))
        many_outputs = {tattler_client_utils.mk_correlation_id() for i in range(1000)}
        self.assertEqual(len(many_outputs), 1000)
