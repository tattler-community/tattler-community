import unittest
from unittest import mock
import urllib
import json
from datetime import datetime

from tattler.client.tattler_py.tattler_client_http import TattlerClientHTTP

class TestTattlerClientHTTP(unittest.TestCase):
    port = 11503

    # a potential valid response from the server
    srv_response = b"""[{
                "id": "email:d696e498-cc1a-4dc8-b893-2070e1b58187",
                "vector": "email",
                "resultCode": 0,
                "detail": "OK"},
                {
                "id": "sms:54aa3973-bd92-4d21-996b-8a1f98e38801",
                "vector": "sms",
                "resultCode": 1,
                "detail": "Error descr 123"}
                ]"""

    def test_notification_construction(self):
        """Constructor succeeds with valid parameters"""
        n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
        self.assertIsNotNone(n)

    def test_notification_construction_invalid_scope(self):
        """Constructor rejects invalid scope parameters"""
        for inv in ['', 'invalid+', 's/', 'perché']:
            with self.assertRaises(ValueError, msg=f"TattlerClientHTTP constructor unexpectedly succeeds with invalid scope name '{inv}'"):
                TattlerClientHTTP(inv, '127.0.0.1', self.port)

    def test_notification_construction_invalid_mode(self):
        """Constructor rejects invalid mode parameters"""
        for inv in ['', 'staging_', 'stagin']:
            with self.assertRaises(ValueError, msg=f"TattlerClientHTTP constructor unexpectedly succeeds with invalid mode name '{inv}'"):
                TattlerClientHTTP('testscope', '127.0.0.1', self.port, mode=inv)
        for inv in ['debug', 'staging', 'production', 'debug ', '   debug  ', 'DEBUG']:
            TattlerClientHTTP('testscope', '127.0.0.1', self.port, mode=inv)

    def test_send_all_parameter(self):
        definitions = {'key1': 'val1', 'key2': 'val2'}
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen().__enter__().read.return_value = self.srv_response
            n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
            res = n.send(['email', 'sms'], 'test_event', 1, context=definitions, priority=True)
            self.assertEqual(res, True)
            self.assertTrue(mreq.Request.mock_calls)
            self.assertTrue(mreq.urlopen.mock_calls)
            req_url = mreq.Request.call_args.args[0]
            # event
            self.assertIn(f'http://127.0.0.1:{self.port}/notification/test_scope/test_event/', req_url)
            # user
            self.assertIn('user=1', req_url)
            # method
            self.assertIn('method', mreq.Request.call_args.kwargs)
            self.assertEqual(mreq.Request.call_args.kwargs['method'].upper(), 'POST')
            # vectors
            self.assertIn('vector=email%2Csms', req_url)
            # mode
            self.assertIn('mode=debug', req_url)
            # data
            self.assertIn('data', mreq.Request.call_args.kwargs)
            sent_data = mreq.Request.call_args.kwargs['data'].decode()
            self.assertEqual(json.loads(sent_data), definitions)
            self.assertIn('headers', mreq.Request.call_args.kwargs)
            self.assertIn('Content-Type', mreq.Request.call_args.kwargs['headers'])
            self.assertEqual('application/json', mreq.Request.call_args.kwargs['headers']['Content-Type'])
    
    def test_send_parameters_encoded(self):
        """Parameters are sent to server in URL-encoded form"""
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen().__enter__().read.return_value = self.srv_response
            n = TattlerClientHTTP('test_scope', '123.32.21.31', self.port)
            n.send(vectors=['sms', 'email'], event='test_event', recipient='+,abc123über')
            mreq.Request.assert_called()
            print(mreq.Request.call_args)
            url = mreq.Request.call_args.args[0]
            self.assertIn(f'//123.32.21.31:{self.port}/notification/test_scope/test_event/?', url)
            self.assertIn('user=%2B%2Cabc123%C3%BCber', url)
            self.assertIn('vector=email%2Csms', url)

    def test_send_all_vectors_fail_yields_failure(self):
        """If notification to every requested vector fails, then the whole notification returns false"""
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen().__enter__().read.return_value = b"""[{
                "id": "email:d696e498-cc1a-4dc8-b893-2070e1b58187",
                "vector": "email",
                "resultCode": 1,
                "detail": "Error descr 4432"},
                {
                "id": "sms:54aa3973-bd92-4d21-996b-8a1f98e38801",
                "vector": "sms",
                "resultCode": 1,
                "detail": "Error descr 123"}
                ]"""
            n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
            res = n.send(['email', 'sms'], 'test_event', 1)
            self.assertEqual(res, False)

    def test_send_receive_no_response(self):
        """If server response is empty, send() returns false"""
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen().__enter__().read.return_value = b""
            n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
            res = n.send(['email', 'sms'], 'test_event', 1)
            self.assertEqual(res, False)

    def test_send_receive_unparsable_response(self):
        """If server response is non-empty but unparsable, send() returns false"""
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen().__enter__().read.return_value = b"""[{"""
            n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
            res = n.send(['email', 'sms'], 'test_event', 1)
            self.assertEqual(res, False)

    def test_send_failure(self):
        """If HTTP request returns a network-level error, send() returns false"""
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            for ertype in [urllib.error.URLError("errormsg123"), urllib.error.HTTPError('url', 500, "errormsg123", {}, None)]:
                mreq.urlopen.side_effect = ertype
                n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
                res = n.send(['email'], 'test_event', 1)
                self.assertTrue(mreq.Request.mock_calls)
                self.assertTrue(mreq.urlopen.mock_calls)
                self.assertEqual(res, False)

    def test_send_complex_obj_serialized(self):
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
            want_time = datetime(2022, 6, 9, 18, 44, 15, 157049)
            want_context = {
                'datetime': want_time,
                'date': want_time.date(),
                'set': {3, 2, 1}
                }
            res = n.send(['email'], 'test_event', 1, context=want_context)
            have_context = json.loads(mreq.Request.call_args.kwargs['data'])
            self.assertIn('datetime', have_context)
            self.assertEqual(have_context['datetime'], want_time.isoformat())
            self.assertIn('date', have_context)
            self.assertEqual(have_context['date'], want_time.date().isoformat())
            self.assertIn('set', have_context)
            self.assertEqual(set(have_context['set']), want_context['set'])

    def test_scopes(self):
        n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            for scopes in [[], ['a'], ['one', 'two']]:
                mreq.urlopen().__enter__().read.return_value = json.dumps(scopes).encode()
                self.assertEqual(n.scopes(), scopes)
                self.assertTrue(mreq.urlopen.call_args)
                want_url = 'http://127.0.0.1:11503/notification/'
                self.assertIn(want_url, mreq.urlopen.call_args.args)
    
    def test_scopes_failure(self):
        n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen.side_effect = urllib.error.URLError("Cannot connect")
            with self.assertRaises(urllib.error.URLError):
                n.scopes()
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen.side_effect = urllib.error.HTTPError('url', 500, "errormsg123", {}, None)
            with self.assertRaises(urllib.error.HTTPError):
                n.scopes()

    def test_events(self):
        n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            for events in [[], ['a'], ['one', 'two']]:
                mreq.urlopen().__enter__().read.return_value = json.dumps(events).encode()
                self.assertEqual(n.events(), events)
                self.assertTrue(mreq.urlopen.call_args)
                want_url = 'http://127.0.0.1:11503/notification/test_scope/'
                self.assertIn(want_url, mreq.urlopen.call_args.args)

    def test_events_failure(self):
        n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen.side_effect = urllib.error.URLError("Cannot connect")
            with self.assertRaises(urllib.error.URLError):
                n.events()
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen.side_effect = urllib.error.HTTPError('url', 400, "Requested scope not provided, valid or existent", {}, None)
            with self.assertRaises(urllib.error.HTTPError):
                n.events()

    def test_vectors(self):
        n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            for events in [[], ['email'], ['email', 'sms', 'telegram']]:
                mreq.urlopen().__enter__().read.return_value = json.dumps(events).encode()
                self.assertEqual(n.vectors('test_event'), events)
                self.assertTrue(mreq.urlopen.call_args)
                want_url = 'http://127.0.0.1:11503/notification/test_scope/test_event/vectors/'
                self.assertIn(want_url, mreq.urlopen.call_args.args)

    def test_vectors_failure(self):
        n = TattlerClientHTTP('test_scope', '127.0.0.1', self.port)
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen.side_effect = urllib.error.URLError("Cannot connect")
            with self.assertRaises(urllib.error.URLError):
                n.vectors('test_event')
        with mock.patch('tattler.client.tattler_py.tattler_client_http.request') as mreq:
            mreq.urlopen.side_effect = urllib.error.HTTPError('url', 400, "Requested scope or event not provided, valid or existent", {}, None)
            with self.assertRaises(urllib.error.HTTPError):
                n.vectors('test_event')


if __name__ == '__main__':
    unittest.main()