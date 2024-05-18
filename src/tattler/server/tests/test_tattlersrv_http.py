"""Tests for tattler HTTP server"""

import os
import logging
import json
import unittest
import unittest.mock
from datetime import datetime
# to run server and test clients in parallel
import threading
import urllib
from urllib.request import Request, urlopen
import urllib.error
from pathlib import Path
from typing import Mapping, Optional

from tattler.server import tattlersrv_http

data_contacts = {
    '123': {
        'email': 'one@two.three',
        'sms': '998877'
        }
    }

def getenv_pseudo(base_env: Mapping[str, Optional[str]], extra_env: Optional[Mapping[str, Optional[str]]]=None):
    """Return a getenv function serving a given set of environments"""
    def getenvf(k: str, v: Optional[str]=None) -> Optional[str]:
        return fullenv.get(k, os.getenv(k, v))
    fullenv = base_env if extra_env is None else {**base_env, **extra_env}
    return getenvf

class TattlerHttpServerTest(unittest.TestCase):
    port = 11503

    def setUp(self):
        self.connstr = f'127.0.0.1:{self.port}'
        self.templatesdir = Path(__file__).parent / 'fixtures' / 'templates_dir'
        self.base_env = {
                'TATTLER_LISTEN_ADDRESS': self.connstr,
                'TATTLER_TEMPLATE_BASE': self.templatesdir,
                'TATTLER_MASTER_MODE': 'production'
            }
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            mgetenv.side_effect = getenv_pseudo(self.base_env)
            logging.info("Setting template base -> %s", self.templatesdir)
            self.server = tattlersrv_http.parse_opts_and_serve()
            if self.server is None:
                raise self.fail("Unable to start server thread. There's likely another server instance running on the same port.")
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            logging.info("starting up server ...")
            self.server_thread.start()
    
    def tearDown(self) -> None:
        logging.info("cleaning up server ...")
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()
        return super().tearDown()

    def mkreq(self, path, data=None, method='GET'):
        url = f'http://{self.connstr}{path}'
        logging.info("Testing '%s' ...", url)
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
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                mgetenv.side_effect = getenv_pseudo(self.base_env)
                mgetenv2.side_effect = mgetenv.side_effect
                with urlopen(url) as f:
                    self.assertEqual(f.status, 200)
                    res = json.loads(f.read().strip())
                    self.assertEqual(set(res), {'jinja', 'testcontext'})

    def test_list_events(self):
        url = self.mkreq('/notification/jinja/')
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                mgetenv.side_effect = getenv_pseudo(self.base_env)
                mgetenv2.side_effect = mgetenv.side_effect
                with urlopen(url) as f:
                    self.assertEqual(f.status, 200)
                    res = json.loads(f.read().strip())
                    self.assertEqual(set(res), {'jinja_event', 'jinja_humanize', 'jinja_variable_expressions', 'jinja_email_and_sms'})

    def test_list_events_wrong_scope(self):
        url = self.mkreq('/notification/inexev123/')
        with self.assertRaises(urllib.error.URLError):
            with urlopen(url):
                pass

    def test_get_details_event_without_vector_suffix_fails(self):
        url = self.mkreq('/notification/jinja/jinja_event/')
        with self.assertRaises(urllib.error.URLError):
            with urlopen(url):
                pass

    def test_get_details_event_inexistent(self):
        url = self.mkreq('/notification/jinja/inexevent98765/')
        with self.assertRaises(urllib.error.URLError):
            with urlopen(url):
                pass

    def test_get_vectors_event_single_result(self):
        url = self.mkreq('/notification/jinja/jinja_event/vectors/')
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                mgetenv.side_effect = getenv_pseudo(self.base_env)
                mgetenv2.side_effect = mgetenv.side_effect
                with urlopen(url) as f:
                    self.assertEqual(f.status, 200)
                    res = json.loads(f.read().strip())
                    self.assertEqual(set(res), {'email'})

    def test_get_vectors_event_multiple_results(self):
        url = self.mkreq('/notification/testcontext/valid_event/vectors/')
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                mgetenv.side_effect = getenv_pseudo(self.base_env)
                mgetenv2.side_effect = mgetenv.side_effect
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
                with urlopen(req):
                    pass

    def test_send_empty_body(self):
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123', method='POST')
        with unittest.mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as ab:
            ab.side_effect = lambda u, y=None: data_contacts[u]
            with unittest.mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
                    with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                        mgetenv.side_effect = getenv_pseudo(self.base_env)
                        mgetenv2.side_effect = mgetenv.side_effect
                        with urlopen(req) as f:
                            self.assertEqual(f.status, 200)

    def test_send_minimal(self):
        defs = {'a': '1', 'b': '2'}
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123', method='POST', data=json.dumps(defs).encode())
        with unittest.mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as ab:
            ab.side_effect = lambda u, y=None: data_contacts[u]
            with unittest.mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
                    with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                        mgetenv.side_effect = getenv_pseudo(self.base_env)
                        mgetenv2.side_effect = mgetenv.side_effect
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
                with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
                    with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                        mgetenv.side_effect = getenv_pseudo(self.base_env)
                        mgetenv2.side_effect = mgetenv.side_effect
                        with urlopen(req) as f:
                            self.assertEqual(f.status, 200)
                            json.loads(f.read().strip())
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
                with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
                    with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                        mgetenv.side_effect = getenv_pseudo(self.base_env)
                        mgetenv2.side_effect = mgetenv.side_effect
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
                with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
                    with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                        mgetenv.side_effect = getenv_pseudo(self.base_env)
                        mgetenv2.side_effect = mgetenv.side_effect
                        with urlopen(req) as f:
                            self.assertEqual(f.status, 200)
                            self.assertTrue(msend.mock_calls)
                            for mcall in msend.mock_calls:
                                vec_name = mcall.args[0]
                                self.assertEqual(set(mcall.args[2]), {data_contacts['123'][vec_name]})

    def test_operating_mode_capped_by_master_mode_setting(self):
        req = self.mkreq('/notification/jinja/jinja_humanize/?user=123', method='POST')
        with unittest.mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as mcontacts:
            with unittest.mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
                    with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                        mcontacts.return_value = data_contacts['123']
                        newenv = {**self.base_env, **{ 'TATTLER_MASTER_MODE': 'debug' }}
                        mgetenv.side_effect = lambda k, v=None: newenv.get(k, os.getenv(k, v))
                        mgetenv2.side_effect = mgetenv.side_effect
                        with urlopen(req):
                            print(msend.mock_calls)
                            msend.assert_called()
                            for c in msend.mock_calls:
                                if 'mode' in c.kwargs:
                                    self.assertEqual('debug', c.kwargs['mode'], msg=f"Tattler expected to limit mode=debug for TATTLER_MASTER_MODE, used {c.kwargs['mode']} instead.")
                                else:
                                    self.assertIn('debug', c.args, msg=f"Tattler expected to limit mode=debug for TATTLER_MASTER_MODE, used arguments {c.args} instead.")

    def test_send_selective_vector(self):
        """Response to a notification request restricted to a vector only includes that vector."""
        req = self.mkreq('/notification/jinja/jinja_email_and_sms/?user=123&vector=email', method='POST')
        with unittest.mock.patch('tattler.server.tattlersrv_http.tattler_utils.pluginloader.lookup_contacts') as mcontacts:
            with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
                with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                    mgetenv.side_effect = getenv_pseudo(self.base_env)
                    mgetenv2.side_effect = mgetenv.side_effect
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
        with unittest.mock.patch('tattler.server.tattlersrv_http.pluginloader.lookup_contacts') as mcontacts:
            mcontacts.return_value = data_contacts['123']
            with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
                with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv2:
                    mgetenv.side_effect = getenv_pseudo(self.base_env)
                    mgetenv2.side_effect = mgetenv.side_effect
                    with self.assertRaises(urllib.error.HTTPError) as err:
                        with urlopen(req):  # to avoid resource leaks
                            pass
                    self.assertEqual(400, err.exception.status)
                    self.assertIn("None of the requested vectors", err.exception.msg)
                    self.assertIn("email", err.exception.msg)

    def test_demotemplates_fallback(self):
        """Demo templates are loaded if no other templates are found"""
        with unittest.mock.patch('tattler.server.tattlersrv_http.tattler_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_TEMPLATE_BASE': None}.get(x, os.getenv(x, y))
            url = self.mkreq('/notification/')
            with urlopen(url) as resp:
                self.assertEqual(resp.status, 200)
                have_resp = json.load(resp)
                self.assertEqual(['demoscope'], list(have_resp))
            # mgetenv.side_effect = ValueError
            want_path = Path(__file__).parent.parent.parent / 'templates'
            # want_path_suffix = PurePath('tattler') / 'templates'
            self.assertEqual(str(want_path), str(tattlersrv_http.tattler_utils.get_template_mgr().base_path))

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

    def test_malformed_request(self):
        """Server responds 404 to malformed requests"""
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattlersrv_http.urlparse') as murlparse:
                murlparse.side_effect = ValueError("Foobar")
                url = self.mkreq('/notification/a/b/', method='POST')
                with self.assertRaises(urllib.error.HTTPError) as err:
                    with urlopen(url):
                        pass
                    self.assertEqual(400, err.exception.status)

    def test_validate_templates_at_startup(self):
        """server calls check_templates_health() and aborts upon errors"""
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattlersrv_http.tattler_utils.check_templates_health') as mcheck:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_LISTEN_ADDRESS': '127.0.0.1:11555'}.get(x, os.getenv(x, y))
                want_exc = ValueError('fooXYZ')
                mcheck.side_effect = want_exc
                with self.assertRaises(ValueError):
                    tattlersrv_http.main()

    def test_server_stops_upon_user_interruption(self):
        """Server stops if user presses Ctrl-C"""
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattlersrv_http.http.server.HTTPServer') as mhttp:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_LISTEN_ADDRESS': '127.0.0.1:11555'}.get(x, os.getenv(x, y))
                mhttp.side_effect = KeyboardInterrupt()
                tattlersrv_http.main()
    
    def test_server_stops_upon_bind_error(self):
        """Server stops with error message if requested socket address cannot be acquired"""
        with unittest.mock.patch('tattler.server.tattlersrv_http.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattlersrv_http.http.server.HTTPServer') as mhttp:
                with unittest.mock.patch('tattler.server.tattlersrv_http.log') as mlog:
                    mgetenv.side_effect = lambda x, y=None: {'TATTLER_LISTEN_ADDRESS': '127.0.0.1:11555'}.get(x, os.getenv(x, y))
                    mhttp.side_effect = OSError()
                    tattlersrv_http.main()
                    mlog.error.assert_called()
                    self.assertIn("Unable to bind", mlog.error.call_args.args[0])
    

if __name__ == '__main__':
    unittest.main()
