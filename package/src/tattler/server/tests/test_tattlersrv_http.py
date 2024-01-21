from pathlib import PurePath
import os
import logging
import urllib
import json
import unittest
import unittest.mock
from datetime import datetime
# to run server and test clients in parallel
import threading
from urllib.request import Request, urlopen
from pathlib import Path
from importlib.abc import Traversable
from importlib.readers import MultiplexedPath

from testutils import get_template_dir

from tattler.server import tattlersrv_http

data_contacts = {
    '123': {
        'email': 'one@two.three',
        'sms': '998877'
        }
    }

class TattlerHttpServerTest(unittest.TestCase):
    port = 11503

    def setUp(self):
        self.connstr = f'127.0.0.1:{self.port}'
        os.environ['TATTLER_LISTEN_ADDRESS'] = self.connstr
        os.environ['TATTLER_TEMPLATE_BASE'] = get_template_dir()
        logging.info("Setting template base -> %s", os.getenv('TATTLER_TEMPLATE_BASE'))
        self.server = tattlersrv_http.parse_opts_and_serve()
        self.server_thread = None
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.orig_env = os.environ.copy()
        os.environ['TATTLER_MASTER_MODE'] = 'production'
        logging.info("starting up server ...")
        self.server_thread.start()
    
    def tearDown(self) -> None:
        logging.info("cleaning up server ...")
        os.environ = self.orig_env
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()
        return super().tearDown()

    def mkreq(self, path, data=None, method='GET'):
        url = f'http://{self.connstr}{path}'
        logging.info(f"Testing {url} ...")
        headers = {}
        if data:
            headers['Content-Type'] = 'application/json'
        req = Request(url=url, data=data, method=method, headers=headers)
        return req

    def test_unknown_paths_rejected(self):
        url = self.mkreq('/notification/a/b/')
        with self.assertRaises(urllib.error.URLError):
            urlopen(url)
        url = self.mkreq('/notification/;')
        with self.assertRaises(urllib.error.URLError):
            urlopen(url)
        req = self.mkreq('/invalid_url/', method='POST')
        with self.assertRaises(urllib.error.URLError):
            with urlopen(req):
                pass

    def test_send_missing_user(self):
        for q in ['', '?user=', '?user=?']:
            req = self.mkreq(f'/notification/a/b/{q}', method='POST')
            with self.assertRaises(urllib.error.URLError):
                with urlopen(req):
                    pass

    def test_send_invalid_vector(self):
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123&vector=unknown', method='POST')
        with unittest.mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
            with self.assertRaises(urllib.error.URLError):
                with urlopen(req):
                    pass

    def test_request_wrong_content_type(self):
        data = json.dumps({'1': 2}).encode('utf-8')
        req = self.mkreq('/notification/a/b/?user=123', data=data, method='POST')
        req.remove_header('Content-Type')
        req.add_header('Content-Type', 'text/csv')
        with self.assertRaises(urllib.error.URLError):
            with urlopen(req):
                pass

    def test_request_broken_json(self):
        data = json.dumps({'1': 2}).encode('utf-8')
        req = self.mkreq('/notification/a/b/?user=123', data=data[:-1], method='POST')
        with self.assertRaises(urllib.error.URLError):
            with urlopen(req):
                pass
    
    def test_list_scopes(self):
        url = self.mkreq('/notification/')
        with urlopen(url) as f:
            self.assertEqual(f.status, 200)
            res = json.loads(f.read().strip())
            self.assertEqual(set(res), {'jinja', 'testcontext'})

    def test_list_events(self):
        url = self.mkreq('/notification/jinja/')
        with urlopen(url) as f:
            self.assertEqual(f.status, 200)
            res = json.loads(f.read().strip())
            self.assertEqual(set(res), {'jinja_event', 'jinja_humanize', 'jinja_variable_expressions', 'jinja_email_and_sms'})

    def test_list_events_wrong_scope(self):
        url = self.mkreq('/notification/inexev123/')
        with self.assertRaises(urllib.error.URLError):
            urlopen(url)

    def test_get_details_event_without_vector_suffix_fails(self):
        url = self.mkreq('/notification/jinja/jinja_event/')
        with self.assertRaises(urllib.error.URLError):
            urlopen(url)

    def test_get_details_event_inexistent(self):
        url = self.mkreq('/notification/jinja/inexevent98765/')
        with self.assertRaises(urllib.error.URLError):
            urlopen(url)

    def test_get_vectors_event_single_result(self):
        url = self.mkreq('/notification/jinja/jinja_event/vectors/')
        with urlopen(url) as f:
            self.assertEqual(f.status, 200)
            res = json.loads(f.read().strip())
            self.assertEqual(set(res), {'email'})

    def test_get_vectors_event_multiple_results(self):
        url = self.mkreq('/notification/testcontext/valid_event/vectors/')
        with urlopen(url) as f:
            self.assertEqual(f.status, 200)
            res = json.loads(f.read().strip())
            self.assertEqual(set(res), {'email', 'sms'})

    def test_send_dberror(self):
        defs = {'a': '1', 'b': '2'}
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123', method='POST', data=json.dumps(defs).encode())
        with unittest.mock.patch('tattler.server.tattler_utils.send_notification_user_vectors') as msend:
            msend.side_effect = Exception
            with self.assertRaises(urllib.error.URLError):
                urlopen(req)

    def test_send_empty_body(self):
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123', method='POST')
        with unittest.mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as ab:
            ab.side_effect = lambda u, y=None: data_contacts[u]
            with unittest.mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                with urlopen(req) as f:
                    self.assertEqual(f.status, 200)

    def test_send_minimal(self):
        defs = {'a': '1', 'b': '2'}
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123', method='POST', data=json.dumps(defs).encode())
        with unittest.mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as ab:
            ab.side_effect = lambda u, y=None: data_contacts[u]
            with unittest.mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                with urlopen(req) as f:
                    self.assertEqual(f.status, 200)
                    self.assertTrue(msend.mock_calls)
                    res = json.loads(f.read().strip())
                    self.assertEqual(type(res), list)
                    for job in res:
                        self.assertIn('id', job)
    
    def test_send_complex_definitions(self):
        want_time = datetime.now()
        defs = {'a': '1', 'b': '2', 'time': want_time.isoformat(), 'date': want_time.date().isoformat()}
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123', method='POST', data=json.dumps(defs).encode())
        with unittest.mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as ab:
            ab.side_effect = lambda u, y=None: data_contacts[u]
            with unittest.mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                with urlopen(req) as f:
                    self.assertEqual(f.status, 200)
                    res = json.loads(f.read().strip())
                    self.assertIn('context', msend.call_args.kwargs)
                    self.assertIn('time', msend.call_args.kwargs['context'])
                    self.assertEqual(msend.call_args.kwargs['context']['time'], want_time)
                    self.assertIn('date', msend.call_args.kwargs['context'])
                    self.assertEqual(msend.call_args.kwargs['context']['date'], want_time.date())

    def test_send_correct_vectors(self):
        want_vectors = {
            'jinja_humanize': {'sms'},
            'jinja_event': {'email'},
            'jinja_email_and_sms': {'email', 'sms'},
        }
        with unittest.mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as ab:
            with unittest.mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                ab.side_effect = lambda u, y=None: data_contacts[u]
                # SMS only, email only, both
                for evname, envval in want_vectors.items():
                    msend.reset_mock()
                    req = self.mkreq(f'/notification/jinja/{evname}/?user=123&mode=staging', method='POST')
                    with urlopen(req) as f:
                        self.assertEqual(f.status, 200)
                        self.assertTrue(msend.mock_calls)
                        call_vectors = {c.args[0] for c in msend.mock_calls}
                        self.assertEqual(call_vectors, envval)
                        for mcall in msend.mock_calls:
                            self.assertIn('mode', mcall.kwargs)
                            self.assertEqual(mcall.kwargs['mode'], 'staging')
                            # vector is not empty
                            self.assertTrue(mcall.args[0])
                            # vector is among user's contacts
                            self.assertIn(mcall.args[0], data_contacts['123'].keys())
    
    def test_send_correct_recipients(self):
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123', method='POST')
        with unittest.mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as ab:
            ab.side_effect = lambda u, role=None: data_contacts[u]
            with unittest.mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                with urlopen(req) as f:
                    self.assertEqual(f.status, 200)
                    self.assertTrue(msend.mock_calls)
                    for mcall in msend.mock_calls:
                        vec_name = mcall.args[0]
                        self.assertEqual(set(mcall.args[2]), {data_contacts['123'][vec_name]})

    def test_operating_mode_capped_by_master_mode_setting(self):
        vname = 'TATTLER_MASTER_MODE'
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123', method='POST')
        with unittest.mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as mcontacts:
            with unittest.mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                mcontacts.return_value = data_contacts['123']
                oldenv = os.getenv(vname)
                os.environ[vname] = 'debug'
                with urlopen(req) as f:
                    print(msend.mock_calls)
                    msend.assert_called()
                    for i, c in enumerate(msend.mock_calls):
                        if 'mode' in c.kwargs:
                            self.assertEqual('debug', c.kwargs['mode'], msg=f"Tattler expected to limit mode=debug for TATTLER_MASTER_MODE, used {c.kwargs['mode']} instead.")
                        else:
                            self.assertIn('debug', c.args, msg=f"Tattler expected to limit mode=debug for TATTLER_MASTER_MODE, used arguments {c.args} instead.")
                    if oldenv is None:
                        del os.environ[vname]
                    else:
                        os.environ[vname] = oldenv

    def test_send_selective_vector(self):
        """Response to a notification request restricted to a vector only includes that vector."""
        req = self.mkreq('/notification/jinja/jinja_email_and_sms/?user=123&vector=email', method='POST')
        with unittest.mock.patch('tattler.server.tattlersrv_http.tattler_utils.pluginloader.lookup_contacts') as mcontacts:
            mcontacts.return_value = data_contacts['123']
            with urlopen(req) as f:
                res = f.read()
                res = json.loads(res)
                self.assertEqual(len(res), 1)
                self.assertIn('vector', res[0])
                self.assertEqual(res[0]['vector'], 'email')

    def test_send_vector_rejected_iff_inexistent(self):
        """Failure if requesting notification to a specific vector which is not supported by the event."""
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123&vector=email', method='POST')
        with unittest.mock.patch('tattler.server.tattlersrv_http.tattler_utils.pluginloader.lookup_contacts') as mcontacts:
            mcontacts.return_value = data_contacts['123']
            with self.assertRaises(urllib.error.HTTPError) as err:
                with urlopen(req):  # to avoid resource leaks
                    pass
            self.assertEqual(400, err.exception.status)
            self.assertIn("None of the requested vectors", err.exception.msg)
            self.assertIn("email", err.exception.msg)

    def test_demotemplates_fallback(self):
        """Demo templates are loaded if no other templates are found"""
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_TEMPLATE_BASE': None}.get(x, os.getenv(x, y))
            # mgetenv.side_effect = ValueError
            want_path = Path(__file__).parent.parent.parent / 'templates'
            # want_path_suffix = PurePath('tattler') / 'templates'
            self.assertEqual(str(want_path), str(tattlersrv_http.get_templates_path()))

    def test_plugins_only_loaded_if_configured(self):
        with unittest.mock.patch('tattler.server.tattlersrv_http.tattler_utils.init_plugins') as minit:
            with unittest.mock.patch('tattler.server.tattlersrv_http.http.server'):
                with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
                    mgetenv.side_effect = lambda x, y=None: {'TATTLER_PLUGIN_PATH': None}.get(x, os.getenv(x, y))
                    tattlersrv_http.main()
                    minit.assert_called_with(None)
                    minit.reset_mock()
                    mgetenv.reset_mock()
                    mgetenv.side_effect = lambda x, y=None: {'TATTLER_PLUGIN_PATH': 'abc'}.get(x, os.getenv(x, y))
                    tattlersrv_http.main()
                    mgetenv.assert_called()
                    minit.assert_called_with('abc')

    def test_main_honors_listening_configuration(self):
        """If passed TATTLER_LISTEN_ADDRESS var, listen to that -- else listen to default"""
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattlersrv_http.tattler_utils.init_plugins'):
                with unittest.mock.patch('tattler.server.tattlersrv_http.serve') as mserve:
                    mgetenv.side_effect = lambda x, y=None: {'TATTLER_LISTEN_ADDRESS': y}.get(x, os.getenv(x, y))
                    tattlersrv_http.main()
                    mserve.assert_called_with('127.0.0.1', 11503)
                    mgetenv.reset_mock()
                    mgetenv.side_effect = lambda x, y=None: {'TATTLER_LISTEN_ADDRESS': '1.2.3.4:45'}.get(x, os.getenv(x, y))
                    tattlersrv_http.main()
                    mserve.assert_called_with('1.2.3.4', 45)

    def test_main_runs(self):
        """main() function runs gracefully with basic configuration parameters"""
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattlersrv_http.http.server.HTTPServer'):
                mgetenv.side_effect = lambda x, y=None: y
                tattlersrv_http.main()

    def test_demo_templates(self):
        """get_template_manager runs if multiple template folders are automatically found"""
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattlersrv_http.files') as mfiles:
                mgetenv.side_effect = lambda k,v=None: {'TATTLER_TEMPLATE_BASE': None}.get(k, os.getenv(k, v))
                p1 = Path(__file__).parent.joinpath('fixtures', 'templates_dir_duplicate', 'templates1')
                p2 = Path(__file__).parent.joinpath('fixtures', 'templates_dir_duplicate', 'templates2')
                mfiles.return_value: Traversable = MultiplexedPath(p1, p2)
                self.assertIsInstance(tattlersrv_http.get_templates_path(), Path)
                self.assertTrue(mfiles.mock_calls)

if __name__ == '__main__':
    unittest.main()