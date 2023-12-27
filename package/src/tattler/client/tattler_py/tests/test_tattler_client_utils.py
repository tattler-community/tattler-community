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


class NetNotifClientUtilsTest(unittest.TestCase):
    def test_get_server_endpoint_raises_if_unset(self):
        with unittest.mock.patch('tattler.client.tattler_py.tattler_client_utils.os.getenv') as mos:
            mos.return_value = None
            with self.assertRaises(RuntimeError):
                tattler_client_utils.get_server_endpoint()

    def test_get_server_endpoint_raises_if_empty(self):
        with unittest.mock.patch('tattler.client.tattler_py.tattler_client_utils.os.getenv') as mos:
            mos.return_value = ''
            with self.assertRaises(RuntimeError):
                tattler_client_utils.get_server_endpoint()

    def test_get_server_endpoint_accepts_address_only_ip4(self):
        with unittest.mock.patch('tattler.client.tattler_py.tattler_client_utils.os.getenv') as mos:
            for _ in range(100):
                want_addr = get_random_ip4()
                mos.return_value = want_addr
                self.assertEqual(tattler_client_utils.get_server_endpoint(), (want_addr, tattler_client_utils.DEFAULT_PORT))

    def test_get_server_endpoint_accepts_address_only_ip6(self):
        with unittest.mock.patch('tattler.client.tattler_py.tattler_client_utils.os.getenv') as mos:
            for _ in range(100):
                want_addr = get_random_ip6()
                mos.return_value = f'[{want_addr}]'
                self.assertEqual(tattler_client_utils.get_server_endpoint(), (want_addr, tattler_client_utils.DEFAULT_PORT))

    def test_get_server_endpoint_accepts_port_only(self):
        with unittest.mock.patch('tattler.client.tattler_py.tattler_client_utils.os.getenv') as mos:
            want_addr = tattler_client_utils.DEFAULT_ADDRESS
            for want_port in [1, 8765]:
                mos.return_value = f":{want_port}"
                self.assertEqual(tattler_client_utils.get_server_endpoint(), (want_addr, want_port))

    def test_get_server_endpoint_accepts_address_ip4_and_port(self):
        with unittest.mock.patch('tattler.client.tattler_py.tattler_client_utils.os.getenv') as mos:
            for want_addr in [get_random_ip4() for i in range(10)]:
                for want_port in [random.randint(1, 65536) for i in range(10)]:
                    mos.return_value = f"{want_addr}:{want_port}"
                    self.assertEqual(tattler_client_utils.get_server_endpoint(), (want_addr, want_port))

    def test_get_server_endpoint_accepts_address_ip6_and_port(self):
        with unittest.mock.patch('tattler.client.tattler_py.tattler_client_utils.os.getenv') as mos:
            for want_addr in [get_random_ip6() for i in range(10)]:
                for want_port in [random.randint(1, 65536) for i in range(10)]:
                    mos.return_value = f"[{want_addr}]:{want_port}"
                    self.assertEqual(tattler_client_utils.get_server_endpoint(), (want_addr, want_port))

    def test_mk_correlation_id_sane_output(self):
        self.assertIsInstance(tattler_client_utils.mk_correlation_id(), str)
        self.assertTrue(tattler_client_utils.mk_correlation_id())
        self.assertGreaterEqual(len(tattler_client_utils.mk_correlation_id()), 6)
        self.assertEqual(len(tattler_client_utils.mk_correlation_id(40)), 40)
        self.assertTrue(tattler_client_utils.mk_correlation_id(prefix='foo').startswith('foo'))
        self.assertTrue(tattler_client_utils.mk_correlation_id(prefix='bar').startswith('bar'))
        self.assertTrue(tattler_client_utils.mk_correlation_id(20, 'bar').startswith('bar'))
        self.assertEqual(len(tattler_client_utils.mk_correlation_id(20, 'bar')), 24)
        many_outputs = {tattler_client_utils.mk_correlation_id() for i in range(1000)}
        self.assertEqual(len(many_outputs), 1000)
