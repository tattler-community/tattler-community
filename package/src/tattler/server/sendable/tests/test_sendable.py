import os
import unittest
import unittest.mock

from tattler.server import sendable

from testutils import temp_envvar, get_lines_without_comments, data_recipients


class SendableTest(unittest.TestCase):
    template_base = os.path.join('fixtures', 'templates')
    blacklist_path = os.path.join('fixtures', 'blacklist.txt')
    recipients = {
        'email': ['support@test123.com'],
        'sms': ['+11234567898', '00417689876']
    }

    def setUp(self):
        os.environ['TATTLER_BULKSMS_TOKEN'] = 'foo:bar'

    def test_notification_id(self):
        all_nids = set()
        for vname, vclass in sendable.vector_sendables.items():
            want_rcpt = data_recipients[vname][0]
            s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base, debug_recipient=want_rcpt)
            self.assertIsInstance(s.nid, str)
            self.assertTrue(s.nid)
            self.assertNotIn(s.nid, all_nids)
            all_nids.add(s.nid)

    def test_modes(self):
        self.assertEqual(sendable.modes, {'debug', 'staging', 'production'})

    def test_sendable_debug_argument(self):
        # debut recipient in constructor
        for vname, vclass in sendable.vector_sendables.items():
            want_rcpt = data_recipients[vname][0]
            with temp_envvar('TATTLER_DEBUG_RECIPIENT_' + vname.upper(), want_rcpt):
                s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base, debug_recipient=want_rcpt)
                self.assertEqual(s.debug_recipient(), want_rcpt)

    def test_sendable_debug_envvar(self):
        # debut recipient in constructor
        for vname, vclass in sendable.vector_sendables.items():
            want_rcpt = data_recipients[vname]
            s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base, debug_recipient=want_rcpt)
            self.assertEqual(s.debug_recipient(), want_rcpt)

    def test_sendable_debug_warns_missing_debugrcpt(self):
        with unittest.mock.patch('tattler.server.sendable.vector_sendable.log') as mlog:
            for vname, vclass in sendable.vector_sendables.items():
                want_rcpt = data_recipients[vname]
                s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base)
                s.send(mode='debug')
                # there's one call logging about this issue
                self.assertTrue(mlog.warning.mock_calls)
                self.assertTrue(any(['TATTLER_DEBUG_RECIPIENT' in c.args[0] for c in mlog.warning.mock_calls]))

    def test_sendable_exists_valid_event(self):
        self.assertTrue(sendable.SMSSendable.exists('event_with_email_and_sms', self.template_base))
        self.assertFalse(sendable.SMSSendable.exists('event_with_email', self.template_base))
        self.assertFalse(sendable.EmailSendable.exists('event_with_email', self.template_base))
        self.assertTrue(sendable.EmailSendable.exists('event_with_email_plain', self.template_base))
        self.assertFalse(sendable.SMSSendable.exists('event_with_email_plain', self.template_base))
    
    def test_sendable_exists_invalid_event(self):
        for vname, vclass in sendable.vector_sendables.items():
            self.assertFalse(vclass.exists('invalid_event', self.template_base))

    def test_sendable_template_base(self):
        for vname, vclass in sendable.vector_sendables.items():
            with self.assertRaises(Exception):
                vclass('event_with_email_and_sms', data_recipients[vname], template_base='inexisting_dir/asdf').content({})

    def test_custom_template_processor(self):
        class CusTempProc:
            def __init__(self, c, **kwargs):
                self.c = c
            def expand(self, ctx, **kwargs):
                return self.c
        for vname, vclass in sendable.vector_sendables.items():
            s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base, template_processor=CusTempProc)
            self.assertNotIn('#1234#', s.content({'one': '#1234#'}))

    def test_raw_content(self):
        for vname, vclass in sendable.vector_sendables.items():
            s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base)
            self.assertNotIn('#1234#', s.raw_content())

    def test_template_expansion(self):
        for vname, vclass in sendable.vector_sendables.items():
            s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base)
            self.assertIn('#1234#', s.content({'one': '#1234#'}))
          
    def test_reject_invalid_recipients(self):
        for vname, vclass in sendable.vector_sendables.items():
            with self.assertRaises(ValueError):
                s = vclass('event_with_email_and_sms', ["#!@#=" + r for r in data_recipients[vname]], template_base=self.template_base)

    def test_blacklist_disabled_until_set(self):
        for vname, vclass in sendable.vector_sendables.items():
            s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base)
            for i in range(100):
                self.assertFalse(s.is_blacklisted(data_recipients[vname][0]+str(i)))

    def test_blacklist_rejects_invalid(self):
        for vname, vclass in sendable.vector_sendables.items():
            s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base)
            s.blacklist(self.blacklist_path)
            bl_items = get_lines_without_comments(self.blacklist_path)
            for bitem in get_lines_without_comments(self.blacklist_path):
                self.assertTrue(s.is_blacklisted(bitem))
            for i in range(100):
                self.assertFalse(s.is_blacklisted(data_recipients[vname][0]+str(i)))
    
    def test_blacklist_reset(self):
        bitems = get_lines_without_comments(self.blacklist_path)
        for vname, vclass in sendable.vector_sendables.items():
            s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base)
            s.blacklist(self.blacklist_path)
            self.assertTrue(s.is_blacklisted(list(bitems)[0]))
            s.blacklist(None)
            self.assertFalse(s.is_blacklisted(list(bitems)[0]))
    
    def test_send_executes_vector(self):
        mocks = {}
        self.assertEqual('sendable', sendable.vector_sendable.Sendable.vector().lower())
        with unittest.mock.patch('tattler.server.sendable.vector_email.EmailSendable.do_send') as e:
            with unittest.mock.patch('tattler.server.sendable.vector_sms.SMSSendable.do_send') as s:
                mocks['email'] = e
                mocks['sms'] = s
                for vname, vclass in sendable.vector_sendables.items():
                    s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base)
                    s.send()
                    mocks[vname].assert_called_once()

    def test_str(self):
        for vname, vclass in sendable.vector_sendables.items():
            s = vclass('event_with_email_and_sms', data_recipients[vname], template_base=self.template_base)
            self.assertIn('event_with_email_and_sms', str(s).lower())
            self.assertIn(vname.lower(), str(s).lower())

    def test_vector(self):
        for vname, vclass in sendable.vector_sendables.items():
            self.assertEqual(vname.lower(), vclass.vector().lower())

    def test_missing_template_raises(self):
        with self.assertRaises(ValueError, msg="SMSSendable doesn't raise for missing template."):
            e = sendable.SMSSendable('event_with_email_plain', data_recipients['sms'], template_base=self.template_base)
            e.content(context={})

    def test_sms_send_triggers_delivery(self):
        with unittest.mock.patch('tattler.server.sendable.vector_sms.BulkSMS') as msms:
            e = sendable.SMSSendable('event_with_email_and_sms', data_recipients['sms'], template_base=self.template_base)
            e.send(context={'one': '1'})
            msms.assert_called()
            with unittest.mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
                e = sendable.EmailSendable('event_with_email_and_sms', data_recipients['email'], template_base=self.template_base)
                e.send(context={'one': '1'})
                self.assertFalse(msms.sendmail.call_args)

    def test_blacklisted_not_sent_to(self):
        blacklisted_rcpt = '+12345678'
        recipients_full = {blacklisted_rcpt, '+29876'}
        recipients_blacklisted = {'+29876'}
        with unittest.mock.patch('tattler.server.sendable.vector_sms.BulkSMS') as msms:
            e = sendable.SMSSendable('event_with_email_and_sms', recipients_full, template_base=self.template_base)
            # send without blacklist
            e.send(context={'one': '1'})
            msms().send.assert_called()
            c_args, _ = msms().send.call_args
            self.assertIn(recipients_full, c_args)
            # send again with blacklist
            e.blacklist(self.blacklist_path)
            e.send(context={'one': '1'})
            msms().send.assert_called()
            c_args, _ = msms().send.call_args
            self.assertNotIn(recipients_full, c_args)
            self.assertIn(recipients_blacklisted, c_args)

    def test_make_notification(self):
        for vname, vclass in sendable.vector_sendables.items():
            n = sendable.make_notification(vname, 'event_with_email_and_sms', data_recipients[vname], template_base=self.template_base)
            self.assertIsNotNone(n)
            self.assertIs(type(n), vclass)
        with self.assertRaises(ValueError):
            sendable.make_notification('invalid_vector', 'event_with_email_and_sms', data_recipients['email'])
    
    def test_send_notification(self):
        for vname, _ in sendable.vector_sendables.items():
            with unittest.mock.patch('tattler.server.sendable.vector_sendable.Sendable.send') as m:
                sendable.send_notification(vname, 'event_with_email_and_sms', data_recipients[vname], template_base=self.template_base, priority='1', mode='production')
                m.assert_called()
                _, c_kwargs = m.call_args
                self.assertIn('priority', c_kwargs)

    def test_send_notification_missing_template(self):
        for vname, _ in sendable.vector_sendables.items():
            with self.assertRaises(ValueError):
                sendable.send_notification(vname, 'missing_event_123', data_recipients[vname], template_base=self.template_base, priority='1', mode='production')
            try:
                sendable.send_notification(vname, 'missing_event_123', data_recipients[vname], template_base=self.template_base, priority='1', mode='production')
            except ValueError as e:
                self.assertIn("template", str(e).lower())

    # tests for delivery mode

    def test_email_delivery_only_to_debug_in_debug_mode(self):
        mocks = {}
        # debug mode = delivery_recipients() is debug address regardless of concrete recipients
        debug_rcpt = 'dev@foo.com'
        supv_rcpt = 'sup@ervisor.com'
        os.environ['TATTLER_DEBUG_RECIPIENT_EMAIL'] = debug_rcpt
        os.environ['TATTLER_SUPERVISOR_RECIPIENT_EMAIL'] = supv_rcpt
        want_rcpts = {
            'production': set(data_recipients['email']),
            'staging': set(data_recipients['email']) | {supv_rcpt},
            'debug': {debug_rcpt}
        }
        with unittest.mock.patch('tattler.server.sendable.vector_email.EmailSendable.do_send') as e:
            for mode in ['production', 'staging', 'debug']:
                s = sendable.vector_sendables['email']('event_with_email_and_sms', data_recipients['email'], template_base=self.template_base)
                s.send(mode=mode, context={'one': '1'})
                self.assertEqual(want_rcpts[mode], s.delivery_recipients(mode), msg=f"Expected recipients {want_rcpts[mode]} != detected {s.delivery_recipients(mode)} match in mode={mode}")
        del os.environ['TATTLER_DEBUG_RECIPIENT_EMAIL']
        del os.environ['TATTLER_SUPERVISOR_RECIPIENT_EMAIL']

    def test_sms_delivery_to_correct_recipients_for_mode(self):
        mocks = {}
        # debug mode = delivery_recipients() is debug address regardless of concrete recipients
        debug_rcpt = '+6898754'
        supv_rcpt = '+5432156'
        os.environ['TATTLER_DEBUG_RECIPIENT_SMS'] = debug_rcpt
        os.environ['TATTLER_SUPERVISOR_RECIPIENT_SMS'] = supv_rcpt
        want_rcpts = {
            'production': set([x.replace('00', '+') for x in data_recipients['sms']]),
            'staging': set([x.replace('00', '+') for x in data_recipients['sms']]) | {supv_rcpt},
            'debug': {debug_rcpt}
        }
        with unittest.mock.patch('tattler.server.sendable.vector_sms.SMSSendable.do_send') as e:
            for mode in ['production', 'staging', 'debug']:
                s = sendable.vector_sendables['sms']('event_with_email_and_sms', data_recipients['sms'], template_base=self.template_base)
                s.send(mode=mode, context={'one': '1'})
                self.assertEqual(want_rcpts[mode], s.delivery_recipients(mode), msg=f"Expected recipients {want_rcpts[mode]} != detected {s.delivery_recipients(mode)} match in mode={mode}")
        del os.environ['TATTLER_DEBUG_RECIPIENT_SMS']
        del os.environ['TATTLER_SUPERVISOR_RECIPIENT_SMS']

    def test_sms_delivery_to_correct_recipients_for_staging_without_supervisor(self):
        # debug mode = delivery_recipients() is debug address regardless of concrete recipients
        supervisor_addrs = {
            'sms': '+5432156',
            'email': 'supervisor_foo@bar.com',
        }
        mode = 'staging'
        with unittest.mock.patch('tattler.server.sendable.vector_email.EmailSendable.do_send'):
            with unittest.mock.patch('tattler.server.sendable.vector_sms.SMSSendable.do_send'):
                for vname, vclass in sendable.vector_sendables.items():
                    supv = supervisor_addrs[vname]
                    actual_recpts = data_recipients[vname]
                    s = vclass('event_with_email_and_sms', actual_recpts, template_base=self.template_base)
                    # with supervisor set
                    envvname = f'TATTLER_SUPERVISOR_RECIPIENT_{vname.upper()}'
                    os.environ[envvname] = supv
                    s.send(mode=mode, context={'one': '1'})
                    want_rcpts = {x.replace('00', '+') for x in actual_recpts} | {supv}
                    self.assertEqual(want_rcpts, s.delivery_recipients(mode), msg=f"Expected {vname} recipients {want_rcpts} != detected {s.delivery_recipients(mode)} match in mode={mode} with envvar {envvname}.")
                    # without supervisor set
                    del os.environ[envvname]
                    s.send(mode=mode, context={'one': '1'})
                    want_rcpts = {x.replace('00', '+') for x in actual_recpts}
                    self.assertEqual(want_rcpts, s.delivery_recipients(mode), msg=f"Expected {vname} recipients {want_rcpts} != detected {s.delivery_recipients(mode)} match in mode={mode} without envvar {envvname}.")


if __name__ == '__main__':
    unittest.main()