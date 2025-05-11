"""Test client utilities"""

import unittest
import unittest.mock
import os
import random
from typing import Any

from tattler.utils.serialization import serialize_json
from tattler.client.tattler_py import tattler_client_utils

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




if __name__ == '__main__':
    unittest.main()         # pragma: no cover
