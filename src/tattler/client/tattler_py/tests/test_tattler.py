import unittest
from unittest import mock

import os
import urllib
import tempfile
from datetime import datetime

from tattler.client.tattler_py.tattler_client import TattlerClient


class TattlerClientTest(unittest.TestCase):
    port = 11503

    def test_default_scopes_empty(self):
        """scopes() for the abstract base class is empty"""
        n = TattlerClient('test_scope', '127.0.0.1', self.port)
        self.assertIsNone(n.scopes())
    
    def test_default_events_raises(self):
        """events() for the abstract base class raises"""
        n = TattlerClient('test_scope', '127.0.0.1', self.port)
        with self.assertRaises(NotImplementedError):
            n.events()

    def test_default_vectors_raises(self):
        """vectors() for the abstract base class raises"""
        n = TattlerClient('test_scope', '127.0.0.1', self.port)
        with self.assertRaises(NotImplementedError):
            n.vectors('asd')

    def test_default_do_send_raises(self):
        """do_send() for the abstract base class raises"""
        n = TattlerClient('test_scope', '127.0.0.1', self.port)
        with self.assertRaises(NotImplementedError):
            n.do_send(None, 'myevent', 'r123')

    def test_server_endpoint_default(self):
        """Constructor supports default server endpoint if none is provided"""
        with mock.patch('tattler.client.tattler_py.tattler_client.TattlerClient.do_send') as mdosend:
            n = TattlerClient('test_scope')
            self.assertEqual(n.endpoint, '127.0.0.1:11503')

    def test_server_endpoint_missing_endpoint_conf_raises(self):
        """Constructor raises exception if server address or port overridden empty"""
        with mock.patch('tattler.client.tattler_py.tattler_client.TattlerClient.do_send') as mdosend:
            with self.assertRaises(ValueError) as err:
                TattlerClient('test_scope', srv_addr=None)
            self.assertIn('ndpoint', str(err.exception))
            with self.assertRaises(ValueError) as err:
                TattlerClient('test_scope', srv_port=None)
            self.assertIn('ndpoint', str(err.exception))

    def test_dead_letter_store_triggered_upon_notification_failure(self):
        n = TattlerClient('test_scope', '127.0.0.1', self.port)
        with mock.patch('tattler.client.tattler_py.tattler_client.TattlerClient.do_send') as mdosend:
            with mock.patch('tattler.client.tattler_py.tattler_client.getenv') as mgetenv:
                mdosend.side_effect = urllib.error.URLError("Cannot connect")
                want_time = datetime(2022, 6, 9, 18, 44, 15, 157049)
                want_context = {
                    'datetime': want_time,
                    'date': want_time.date(),
                    'set': {3, 2, 1}
                    }
                # cleanup any existing deadletter path, to ensure it's created
                with tempfile.TemporaryDirectory() as tmpd:
                    mgetenv.side_effect = lambda k,v=None: {'TATTLER_DEADLETTER_PATH': tmpd}.get(k, os.getenv(k, v))
                    res = n.send(['email'], 'test_event', 1, context=want_context)
                    self.assertFalse(res)
                    # deadletter folder exists
                    self.assertTrue(os.path.exists(tmpd))
                    # there's one file in it
                    deadletters = os.listdir(tmpd)
                    self.assertTrue(deadletters)
                    self.assertEqual(1, len(deadletters))
                    # filename contains scope name
                    self.assertTrue(all(['test_scope' in x for x in deadletters]))
                    # filename contains event name
                    self.assertTrue(all(['test_event' in x for x in deadletters]))
                    # filename contains recipient
                    self.assertTrue(all(['_1' in x for x in deadletters]))
        
    def test_dead_letter_survives_permission_errors_creating_path(self):
        """If deadletter is triggered but fails permissions, no exception is raised"""
        n = TattlerClient('test_scope', '127.0.0.1', self.port)
        with mock.patch('tattler.client.tattler_py.tattler_client.TattlerClient.do_send') as mdosend:
            with mock.patch('tattler.client.tattler_py.tattler_client.getenv') as mgetenv:
                mdosend.side_effect = urllib.error.URLError("Cannot connect")
                mgetenv.side_effect = lambda k,v=None: {'TATTLER_DEADLETTER_PATH': os.path.join(os.sep, 'foo') }.get(k, os.getenv(k, v))
                want_time = datetime(2022, 6, 9, 18, 44, 15, 157049)
                want_context = {
                    'datetime': want_time,
                    'date': want_time.date(),
                    'set': {3, 2, 1}
                    }
                n.send(['email'], 'test_event', 1, context=want_context)

    def test_dead_letter_survives_permission_errors(self):
        """If deadletter is triggered but fails permissions, no exception is raised"""
        n = TattlerClient('test_scope', '127.0.0.1', self.port)
        with mock.patch('tattler.client.tattler_py.tattler_client.TattlerClient.do_send') as mdosend:
            with mock.patch('tattler.client.tattler_py.tattler_client.getenv') as mgetenv:
                mdosend.side_effect = urllib.error.URLError("Cannot connect")
                mgetenv.side_effect = lambda k,v=None: {'TATTLER_DEADLETTER_PATH': os.sep }.get(k, os.getenv(k, v))
                want_time = datetime(2022, 6, 9, 18, 44, 15, 157049)
                want_context = {
                    'datetime': want_time,
                    'date': want_time.date(),
                    'set': {3, 2, 1}
                    }
                n.send(['email'], 'test_event', 1, context=want_context)
