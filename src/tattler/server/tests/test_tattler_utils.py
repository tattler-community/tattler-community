"""Tests for tattler utils"""

import unittest
import os
from unittest import mock
from pathlib import Path
from importlib.abc import Traversable
from tattler.server.tests.testutils import get_template_dir

from tattler.server import tattler_utils

data_contacts = {
    '123': {
        'email': 'foo@bar.com',
        'sms': '998877',
        'account_type': 'pro'
        },
    '456': {
        'email': 'user456@dom.ch'
        },
    '789': {
        'email': 'user789-blacklisted@dom.ch'
        },
    '999': {
        'email': 'multilingual@bar.com',
        'sms': '667788',
        'account_type': 'free',
        'telegram': '1235456',
        'language': 'de_CH',
        },
    }


class TestTattlerUtils(unittest.TestCase):
    blacklist_path = Path(__file__).parent / 'fixtures' / 'blacklist.txt'

    def test_mk_correlation_id(self):
        """mk_correlation_id() produces a minimum length and entropy"""
        for i in range(100):
            cid = tattler_utils.mk_correlation_id(None)
            self.assertIsInstance(cid, str, msg=f"{i}th call to mk_correlation_id() returned non-string")
            self.assertGreaterEqual(len(cid), 10, msg=f"{i}th call to mk_correlation_id() returned ID shorter than 10 = '{cid}'")
            self.assertGreaterEqual(len(set(cid)), 6, msg=f"{i}th call to mk_correlation_id() returned insufficient entropy {len(set(cid))} for '{cid}'")
    
    def test_mk_correlation_id_with_prefix(self):
        """mk_correlation_id() produces IDs prefixed by requested or default prefix"""
        cid = tattler_utils.mk_correlation_id('x')
        self.assertIsInstance(cid, str)
        self.assertTrue(cid.startswith('x:'))

    def test_send_notification_missing_scope(self):
        """Notify missing scope raises ValueError, mentions scope"""
        with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
            msend.side_effect = ValueError("Template does not exist")
            with self.assertRaises(FileNotFoundError) as err:
                tattler_utils.send_notification_user_vectors('123', ['email'], 'missing_scope', 'foobar_event')
            self.assertIn("Scope does not exist", str(err.exception))
            self.assertIn("missing_scope", str(err.exception))

    def test_send_notification_missing_event(self):
        """Notify missing event in existing scope raises ValueError, mentnions event"""
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
            with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                msend.side_effect = ValueError("Template does not exist")
                with self.assertRaises(ValueError) as err:
                    tattler_utils.send_notification_user_vectors('123', ['email'], 'jinja', 'missing_template_123')
                self.assertIn("Event does not exist", str(err.exception))
                self.assertIn("missing_template_123", str(err.exception))

    def test_send_notification_unknown_recipient(self):
        """Notify valid scope and event to missing recipient raises ValueError, mentions recipient"""
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
            with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
                maddrb.return_value = None
                with self.assertRaises(ValueError) as err:
                    tattler_utils.send_notification_user_vectors('123', ['email'], 'jinja', 'jinja_event')
                self.assertIn("Recipient unknown", str(err.exception))
                self.assertIn("123", str(err.exception))
        
    def test_send_notification_invalid_mode(self):
        """Valid notification with invalid mode raises ValueError, mentions mode"""
        with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
            with self.assertRaises(ValueError) as err:
                tattler_utils.send_notification_user_vectors('123', ['email'], 'jinja', 'jinja_event', mode='notexistent')
            self.assertIn("mode", str(err.exception))
            self.assertIn("notexistent", str(err.exception))

    def test_send_notification_includes_extra_variables(self):
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
            with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
                maddrb.return_value = data_contacts['123']
                with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                    tattler_utils.send_notification_user_vectors('123', ['email'], 'jinja', 'jinja_event')
                    self.assertTrue(msend.mock_calls)
                    self.assertIn('context', msend.call_args.kwargs)
                    extra_variables = {
                        # name: want
                        'user_id': '123',
                        'user_email': data_contacts['123']['email'],
                        'user_sms': data_contacts['123']['sms'],
                        'user_firstname': data_contacts['123']['email'].split('@', 1)[0].lower().capitalize(),
                        'user_account_type': 'pro',
                        'user_language': None,
                        'correlation_id': None,
                        'notification_id': None,
                        'notification_mode': 'debug',
                        'notification_vector': None,
                        'notification_scope': 'jinja',
                        'event_name': 'jinja_event'
                        }
                    for varname, varval in extra_variables.items():
                        self.assertIn(varname, msend.call_args.kwargs['context'])
                        if extra_variables[varname] is not None:
                            self.assertEqual(msend.call_args.kwargs['context'][varname], varval)

    def test_send_notification_fills_out_first_name(self):
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
            with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
                maddrb.return_value = data_contacts['123'].copy()
                with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                    for email in ['123@google.com', 'invalidemail']:
                        maddrb.return_value['email'] = email
                        tattler_utils.send_notification_user_vectors('123', ['email'], 'jinja', 'jinja_event')
                        self.assertTrue(msend.mock_calls)
                        self.assertIn('context', msend.call_args.kwargs)
                        self.assertIn('user_firstname', msend.call_args.kwargs['context'])
                        self.assertEqual('user', msend.call_args.kwargs['context']['user_firstname'], msg=f"Guessed first name is not None by invalid email '{email}'")

    def test_send_only_to_available_vectors(self):
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
            with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
                maddrb.return_value = data_contacts['123']
                with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                    tattler_utils.send_notification_user_vectors('123', None, 'jinja', 'jinja_event')
                    self.assertEqual(msend.call_count, 1)
                    self.assertIn('email', msend.call_args.args)
                    self.assertNotIn('sms', msend.call_args.args)

    def test_send_returns_expected_fields(self):
        """send_notification_user_vectors returns all expected fields"""
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
                maddrb.return_value = data_contacts['123']
                mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
                with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                    res = tattler_utils.send_notification_user_vectors('123', None, 'jinja', 'jinja_email_and_sms')
                    self.assertIsInstance(res, list)
                    for itemres in res:
                        self.assertIsInstance(itemres, dict)
                        itemres: dict = itemres
                        self.assertLessEqual({'id', 'vector', 'resultCode', 'result', 'detail'}, set(itemres.keys()))
                    self.assertLessEqual({'email', 'sms'}, {x['vector'] for x in res}, msg=f"Expected result for notification vector 'email', but only got {[x['vector'] for x in res]}")
                    self.assertEqual({'success'}, {x['result'] for x in res}, msg=f"Expected all-successful results, but got {[x['result'] for x in res]}")
                    self.assertEqual({0}, {x['resultCode'] for x in res}, msg=f"Expected all resultCode = 0, but got {[x['resultCode'] for x in res]}")

    def test_send_failure_returns_correct_error(self):
        """send_notification_user_vectors returns error for correct failing vector"""
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
            with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
                maddrb.return_value = data_contacts['123']
                with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                    errmsg = "connection reset"
                    msend.side_effect = OSError(errmsg)
                    res = tattler_utils.send_notification_user_vectors('123', None, 'jinja', 'jinja_email_and_sms')
                    self.assertIsInstance(res, list)
                    for itemres in res:
                        self.assertIsInstance(itemres, dict)
                        itemres: dict = itemres
                        self.assertLessEqual({'id', 'vector', 'resultCode', 'result', 'detail'}, set(itemres.keys()))
                    self.assertLessEqual({'email', 'sms'}, {x['vector'] for x in res}, msg=f"Expected result for notification vector 'email', but only got {[x['vector'] for x in res]}")
                    self.assertEqual({'error'}, {x['result'] for x in res}, msg=f"Expected all-error results, but got {[x['result'] for x in res]}")
                    self.assertEqual({1}, {x['resultCode'] for x in res}, msg=f"Expected all resultCode = 1, but got {[x['resultCode'] for x in res]}")
                    self.assertEqual({"connection reset"}, {x['detail'] for x in res}, msg=f"Expected error detail to contain '{errmsg}', but got {[x['detail'] for x in res]}")

    def test_send_notification_user_vectors_does_not_deliver_to_blacklisted_addresses(self):
        with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
                with mock.patch('tattler.server.tattler_utils.sendable.vector_email.EmailSendable.do_send') as msend:
                    with mock.patch('tattler.server.tattler_utils.getenv') as mgenv:
                        maddrb.side_effect = lambda x: data_contacts.get(x, None)
                        # delivers without blacklist
                        mgenv.side_effect = lambda x, y=None: { 'TATTLER_BLACKLIST_PATH': None, 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
                        tattler_utils.send_notification_user_vectors('456', None, 'jinja', 'jinja_event', mode='production')
                        self.assertEqual(msend.call_count, 1)
                        self.assertIn({data_contacts['456']['email']}, msend.call_args.args)
                        # does not deliver with blacklist to blacklisted addr
                        msend.reset_mock()
                        maddrb.return_value = data_contacts['456']
                        mgenv.side_effect = lambda x, y=None: { 'TATTLER_BLACKLIST_PATH': str(self.blacklist_path), 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
                        tattler_utils.send_notification_user_vectors('789', None, 'jinja', 'jinja_event', mode='production')
                        self.assertEqual(msend.call_count, 0)
                        # delivers with blacklist to legitimate addr
                        msend.reset_mock()
                        tattler_utils.send_notification_user_vectors('456', None, 'jinja', 'jinja_event', mode='production')
                        self.assertEqual(msend.call_count, 1)

    def test_send_trims_notification_id_from_correlation_id(self):
        with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
            maddrb.return_value = data_contacts['123']
            with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
                with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                    mgetenv.side_effect = lambda k, v=None: {'TATTLER_TEMPLATE_BASE': get_template_dir()}.get(k, os.getenv(k, v))
                    corrId = "sys1:sys2:CorrelationIDStringTooLongForNotification"
                    tattler_utils.send_notification_user_vectors('123', ['email'], 'jinja', 'jinja_event', {},
                        correlationId=corrId)
                    msend.assert_called()
                    self.assertIn('context', msend.call_args.kwargs)
                    extra_variables = {
                        # name: want
                        'correlation_id': corrId,
                        'notification_id': corrId.rsplit(':', 1)[1][-tattler_utils.max_notification_id_len:],
                        }
                    for varname, varval in extra_variables.items():
                        self.assertIn(varname, msend.call_args.kwargs['context'])
                        if varval is not None:
                            self.assertEqual(msend.call_args.kwargs['context'][varname], varval, msg=f"Variable {varname} does not match:")

    def test_get_operating_mode_fails_when_master_mode_invalid(self):
        with mock.patch('tattler.server.tattler_utils.os') as mos:
            mos.getenv.return_value = 'invalid_master_mode___'
            with self.assertRaises(RuntimeError):
                tattler_utils.get_operating_mode('debug', 'debug')

    def test_get_operating_mode_fails_when_requested_mode_invalid(self):
        with mock.patch('tattler.server.tattler_utils.os') as mos:
            mos.getenv.return_value = 'invalid_mode___'
            with self.assertRaises(RuntimeError):
                tattler_utils.get_operating_mode('invalid_requested_mode__', 'debug')

    def test_get_operating_mode_caps_requested_mode_to_master_default(self):
        with mock.patch('tattler.server.tattler_utils.os') as mos:
            mos.getenv.return_value = None
            want_mode = 'debug'
            have_mode = tattler_utils.get_operating_mode('production', 'debug')
            self.assertEqual(have_mode, want_mode)

    def test_get_operating_mode_caps_requested_mode_to_master_envvar(self):
        with mock.patch('tattler.server.tattler_utils.os') as mos:
            for m in ['debug', 'staging']:
                mos.getenv.return_value = m
                want_mode = mos.getenv.return_value
                have_mode = tattler_utils.get_operating_mode('production', 'production')
                self.assertEqual(have_mode, want_mode)

    def test_native_plugins_are_initialized_last(self):
        """Native plugins are initialized after user-requested plugins"""
        with mock.patch('tattler.server.tattler_utils.pluginloader.init') as mpinit:
            tattler_utils.init_plugins('.')
            mpinit.assert_called_with(['.'] + [str(x) for x in tattler_utils.native_plugins_path])

    def test_invalid_plugin_directory_ignored(self):
        """Plug-in loading ignores and warns about invalid plug-in paths"""
        with mock.patch('tattler.server.tattler_utils.pluginloader.init') as mpinit:
            with mock.patch('tattler.server.tattler_utils.log') as mlog:
                tattler_utils.init_plugins('foobar')
                mlog.warning.assert_called()
                self.assertTrue(mlog.warning.call_args.args)
                self.assertIn('not a directory', mlog.warning.call_args.args[0])
                mpinit.assert_called_with([str(x) for x in tattler_utils.native_plugins_path])

    def test_plugins_are_initialized_from_correct_path(self):
        tattler_utils.init_plugins(Path(__file__).parent / 'fixtures' / 'plugins_integration')
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
            with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
                with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                    maddrb.return_value = data_contacts['123']
                    tattler_utils.send_notification_user_vectors('123', ['email'], 'jinja', 'jinja_event')
                    self.assertTrue(msend.mock_calls)
                    self.assertIn('context', msend.call_args.kwargs)
                    self.assertIn('foo', msend.call_args.kwargs['context'])
                    self.assertEqual(123, msend.call_args.kwargs['context']['foo'])
                    self.assertIn('bar', msend.call_args.kwargs['context'])
                    self.assertEqual(345, msend.call_args.kwargs['context']['bar'])

    def test_demo_templates(self):
        """get_template_mgr runs if multiple template folders are automatically found"""
        with unittest.mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.tattler_utils.files') as mfiles:
                mgetenv.side_effect = lambda k,v=None: {'TATTLER_TEMPLATE_BASE': None}.get(k, os.getenv(k, v))
                mfiles.return_value = mock.MagicMock(spec=Traversable)
                mfiles.return_value.joinpath.return_value = Path(__file__).parent.joinpath('fixtures', 'templates_dir_duplicate', 'templates1')
                have = tattler_utils.check_templates_health()
                self.assertIsInstance(have, Path)
                self.assertTrue(mfiles.mock_calls)

    def test_plugins_are_passed_correct_context(self):
        tattler_utils.init_plugins(Path(__file__).parent / 'fixtures' / 'plugins_integration')
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
            with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
                maddrb.return_value = data_contacts['123']
                with mock.patch('tattler.server.tattler_utils.pluginloader.process_context') as mproc:
                    with mock.patch('tattler.server.tattler_utils.sendable.send_notification') as msend:
                        ctx = {
                            'one': 1,
                            'two': 'two'
                        }
                        tattler_utils.send_notification_user_vectors('123', ['email'], 'jinja', 'jinja_event', ctx)
                        mproc.assert_called_once()
                        received_ctx = mproc.call_args[0][0]
                        self.assertEqual(ctx, {k:v for k, v in received_ctx.items() if k in ctx})

    def test_name_phony(self):
        suff = '@d.org'
        for un in ('info', 'mail', 'noc', 'webmaster', 'root', 'hostmaster', 'sysadmin', 'postmaster', 'dns', 'ns', 'abuse', 'admin', 'hello', 'hi', 'it'):
            email = un + suff
            self.assertIsNone(tattler_utils.guess_first_name(email), msg=f"Email {email} unexpectedly returns valid user name.")

    def test_name_malformed_addresses(self):
        for email in ['', '@', '@foo.com', 'asd', 'a@a@a']:
            with self.assertRaises(ValueError, msg=f"Email '{email}' expected to raise, but does not."):
                tattler_utils.guess_first_name(email)

    def test_name_capitalized(self):
        for email in ['asd@foo.com', 'Asd@foo.com']:
            self.assertEqual(tattler_utils.guess_first_name(email), 'Asd')
            self.assertEqual(tattler_utils.guess_first_name(email), 'Asd')

    def test_name_omits_numeric_prefix_and_suffix(self):
        for pref in ['foobar123', '123foobar', '123foobar123']:
            email = f'{pref}@x.com'
            self.assertEqual(tattler_utils.guess_first_name(email), 'Foobar')
        email = 'foo2bar@x.com'
        self.assertEqual(tattler_utils.guess_first_name(email), 'Foo2bar')

    def test_check_templates_health_logs_upon_missing_templates_dir(self):
        """check_templates_health() logs error when given templates dir is missing"""
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            with mock.patch('tattler.server.tattler_utils.TemplateMgr') as mtemp:
                with mock.patch('tattler.server.tattler_utils.log') as mtman:
                    mtemp.side_effect = FileNotFoundError("bad XYZ")
                    mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
                    with self.assertRaises(FileNotFoundError) as err:
                        tattler_utils.check_templates_health()
                    mtman.error.assert_called_once()
                    self.assertEqual(err.exception, mtemp.side_effect)
                    self.assertIn('failed health check', mtman.error.call_args.args[0])

    def test_check_templates_health_logs_upon_broken_templates(self):
        """check_templates_health() logs error when some template is malformed"""
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            with mock.patch('tattler.server.tattler_utils.TemplateMgr.validate_templates') as mtemp:
                with mock.patch('tattler.server.tattler_utils.log') as mtman:
                    mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
                    mtemp.side_effect = ValueError("bad XYZ")
                    with self.assertRaises(ValueError) as err:
                        tattler_utils.check_templates_health()
                    mtman.error.assert_called_once()
                    self.assertEqual(err.exception, mtemp.side_effect)
                    self.assertIn('malformed', mtman.error.call_args.args[0])

    def test_check_templates_health_logs_upon_bad_config(self):
        """check_templates_health() logs error when configuration is partial or malformed"""
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            with mock.patch('tattler.server.tattler_utils.TemplateMgr.validate_configuration') as mtemp:
                with mock.patch('tattler.server.tattler_utils.log') as mtman:
                    mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
                    mtemp.side_effect = ValueError("bad XYZ")
                    with self.assertRaises(ValueError) as err:
                        tattler_utils.check_templates_health()
                    mtman.error.assert_called_once()
                    self.assertEqual(err.exception, mtemp.side_effect)
                    self.assertIn('Issues found in configuration', mtman.error.call_args.args[0])

    def test_multilingual_warning(self):
        """Warn if addressbook returns custom language but tattler isn't multilingual"""
        with mock.patch('tattler.server.tattler_utils.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: { 'TATTLER_TEMPLATE_BASE': get_template_dir() }.get(x, os.getenv(x, y))
            with mock.patch('tattler.server.tattler_utils.pluginloader.lookup_contacts') as maddrb:
                maddrb.return_value = data_contacts['999']
                with mock.patch('tattler.server.tattler_utils.log') as mlog:
                    tattler_utils.send_notification_user_vectors('999', ['email'], 'jinja', 'jinja_event')
                    mlog.warning.assert_called()
                    self.assertIn('multilingual', mlog.warning.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
