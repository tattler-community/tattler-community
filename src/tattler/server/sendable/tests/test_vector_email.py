"""Tests for email vector sendable"""

import unittest
from unittest import mock
import os
import re
import random

from pathlib import Path

from tattler.server.sendable.vector_email import EmailSendable, get_smtp_server

data_recipients = {
    'email': ['support@test123.com'],
    'sms': ['+11234567898', '00417689876']
}

# template fixtures generic to multiple vectors
tbase_standard_path = Path(__file__).parent / 'fixtures' / 'templates'
tbase_originalnaming_path = Path(__file__).parent / 'fixtures' / 'templates_originalnaming'
# template fixtures specific to this vector
tbase_path = Path(__file__).parent / 'fixtures' / 'templates_with_base'

class TestVectorEmail(unittest.TestCase):

    def test_content_with_base(self):
        """Sendable can be constructed and content() called"""
        s = EmailSendable('event1', ['foo@bar.com'], template_base=tbase_path)
        s.content(context={})

    def test_send_with_ipv6(self):
        """IPv6 address for SMTP SERVER is supported"""
        s = EmailSendable('event1', ['foo@bar.com'], template_base=tbase_path)
        srvaddr_want = '12:34::1'
        with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_ADDRESS': f"[{srvaddr_want}]:25" }.get(k, os.getenv(k, v))
            with mock.patch('tattler.server.sendable.vector_email.smtplib') as msmtp:
                s.send()
                self.assertTrue(msmtp.SMTP.mock_calls)
                self.assertEqual(msmtp.SMTP.call_args.args[0], srvaddr_want)
    
    def test_send_invalid_server(self):
        """Passing an invalid SMTP server address raises ValueError"""
        s = EmailSendable('event1', ['foo@bar.com'], template_base=tbase_path)
        with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_ADDRESS': "['12:34::1']:25" }.get(k, os.getenv(k, v))
            with mock.patch('tattler.server.sendable.vector_email.smtplib') as msmtp:
                with self.assertRaises(ValueError):
                    s.send()

    def test_send_priority_numeric(self):
        """When a valid (integer) priority is provided, it's applied into the headers of the email delivered"""
        s = EmailSendable('event1', ['foo@bar.com'], template_base=tbase_path)
        with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_ADDRESS': "127.0.0.1:25" }.get(k, os.getenv(k, v))
            with mock.patch('tattler.server.sendable.vector_email.smtplib') as msmtp:
                # numeric
                for prio in [1, 2, 3, 4, 5]:
                    s.send(priority=prio)
                    self.assertTrue(msmtp.SMTP().sendmail.mock_calls)
                    self.assertEqual(len(msmtp.SMTP().sendmail.call_args.args) + len(msmtp.SMTP().sendmail.call_args.kwargs), 3)
                    msg_body = msmtp.SMTP().sendmail.call_args.args[2]
                    prio_want = f'X-Priority: {prio}'
                    self.assertIn(prio_want, msg_body)

    def test_send_priority_bool(self):
        """When a valid (boolean) priority is provided, it's applied as a numeric value into the headers of the email delivered"""
        s = EmailSendable('event1', ['foo@bar.com'], template_base=tbase_path)
        with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_ADDRESS': '127.0.0.1' }.get(k, os.getenv(k, v))
            with mock.patch('tattler.server.sendable.vector_email.smtplib') as msmtp:
                # boolean
                s.send(priority=True)
                self.assertTrue(msmtp.SMTP().sendmail.mock_calls)
                self.assertEqual(len(msmtp.SMTP().sendmail.call_args.args) + len(msmtp.SMTP().sendmail.call_args.kwargs), 3)
                msg_body = msmtp.SMTP().sendmail.call_args.args[2]
                self.assertIn('X-Priority: 1', msg_body)
                # False = default priority
                s.send(priority=False)
                msg_body = msmtp.SMTP().sendmail.call_args.args[2]
                self.assertIn('X-Priority: 3', msg_body)

    def test_send_priority_invalid(self):
        """When an invalid value is provided for priority, an exception is raised."""
        s = EmailSendable('event1', ['foo@bar.com'], template_base=tbase_path)
        with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_ADDRESS': '127.0.0.1' }.get(k, os.getenv(k, v))
            with mock.patch('tattler.server.sendable.vector_email.smtplib') as msmtp:
                with self.assertRaises(ValueError):
                    s.send(priority=100)

    def test_email_priority(self):
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
            # priority file only
            e.send(context={'one': '1'})
            msmtp.assert_called()
            c_args, _ = msmtp().sendmail.call_args
            self.assertTrue(any('X-Priority: 1' in x for x in c_args))
            # with priority parameter
            e.send(context={'one': '1'}, priority='2')
            msmtp.assert_called()
            c_args, _ = msmtp().sendmail.call_args
            self.assertTrue(any('X-Priority: 2' in x for x in c_args))
            # with invalid priority param
            with self.assertRaises(ValueError):
                e.send(context={'one': '1'}, priority='invalid_value')

    def test_email_plain(self):
        """Plain email contains no HTML declaration"""
        e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
        self.assertNotIn('HTML', e.content(context={}))
        self.assertNotIn('html', e.content(context={}))
        self.assertIn('Message-ID:', e.content(context={}))

    def test_email_html(self):
        """HTML email contains text/html part"""
        e = EmailSendable('event_with_email_and_sms', data_recipients['email'], template_base=tbase_standard_path)
        self.assertIn('''Content-Type: text/html; charset=''', e.content(context={'one': '#1234#'}))

    def test_email_html_old_filename_format(self):
        """HTML email contains text/html part, when specified with old filename format body_html"""
        e = EmailSendable('event_with_email_and_sms', data_recipients['email'], template_base=tbase_originalnaming_path)
        self.assertIn('''Content-Type: text/html; charset=''', e.content(context={'one': '#1234#'}))

    def test_new_filename_scheme_prevails(self):
        """If both files body.html and body_plain exist, the former (newer) is picked"""
        e = EmailSendable('event_with_old_and_new_filename_schemes', data_recipients['email'], template_base=tbase_originalnaming_path)
        self.assertIn('new filename scheme', e.subject(context={'one': '#1234#'}))
        self.assertNotIn('old filename scheme', e.subject(context={'one': '#1234#'}))
        self.assertIn('new filename scheme', e.content(context={'one': '#1234#'}))
        self.assertNotIn('old filename scheme', e.content(context={'one': '#1234#'}))

    def test_html_and_plain_place_html_last(self):
        """If a HTML part is present, it is marked as preferred by being placed last, as per RFC 1341"""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            e = EmailSendable('event_with_email_and_sms', data_recipients['email'], template_base=tbase_standard_path)
            e.send(context={'one': 'asd'})
            msmtp.assert_called()
            msmtp.return_value.sendmail.assert_called_once()
            msgtext = msmtp.return_value.sendmail.call_args.args[2]
            regex_html_after_plain = re.compile('^Content-Type: text/plain; .*Content-Type: text/html;', re.MULTILINE | re.DOTALL)
            self.assertIsNotNone(regex_html_after_plain.search(msgtext))

    def test_message_id_uses_sender_domain(self):
        """Message-Id uses domain of sender"""
        with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda k,v=None: { 'TATTLER_EMAIL_SENDER': 'foo@aksjdfhksadf.com' }.get(k, os.getenv(k, v))
            e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
            self.assertIn('Message-ID:', e.content(context={}))
            msgidline = [line for line in e.content(context={}).splitlines() if line.startswith('Message-ID:')][0]
            msgid = msgidline.split(' ', 1)[1]
            self.assertEqual(msgid[0], '<')
            self.assertEqual(msgid[-1], '>')
            self.assertIn('@', msgid)
            domain = msgid.split('@', 1)[1]
            self.assertEqual(domain, 'aksjdfhksadf.com>')

    def test_email_send_triggers_delivery(self):
        """send() calls smtp().sendmail()"""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
            e.send()
            msmtp.assert_called()
            msmtp.return_value.sendmail.assert_called_once()
            self.assertIn('Plain text', msmtp.return_value.sendmail.call_args.args[2])
            self.assertIn('Subject: Subject', msmtp.return_value.sendmail.call_args.args[2])
            msmtp.return_value.starttls.assert_not_called()
    
    def test_email_delivery_tls_connection_if_tls_port(self):
        """If TATTLER_SMTP_ADDRESS includes a well-known port of SMTP TLS service, connect with SMTP_SSL"""
        tls_ports = [465, 587]
        non_tls_ports = [25, 2525]
        addresses = ['12.34.56.78', '[a::b]', 'foo.bar.com']
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP_SSL') as msmtps:
                e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
                with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
                    for addr in addresses:
                        for port in tls_ports+non_tls_ports:
                            mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_ADDRESS': f"{addr}:{port}" }.get(k, os.getenv(k, v))
                            e.send()
                            if port in tls_ports:
                                msmtp.assert_not_called()
                                msmtps.assert_called_once()
                                self.assertIn('timeout', msmtps.call_args.kwargs)
                                self.assertIsNotNone(msmtps.call_args.kwargs['timeout'])
                            else:
                                msmtps.assert_not_called()
                                msmtp.assert_called_once()
                                self.assertIn('timeout', msmtp.call_args.kwargs)
                                self.assertIsNotNone(msmtp.call_args.kwargs['timeout'])
                            msmtp.reset_mock()
                            msmtps.reset_mock()

    def test_email_delivery_timeout(self):
        """Setting TATTLER_SMTP_TIMEOUT envvar controls timeout param to SMTP connection"""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
            with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
                # use random number to avoid inadvertently matching default value
                rndval = random.randint(1, 100)
                mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_TIMEOUT': rndval }.get(k, os.getenv(k, v))
                e.send()
                msmtp.assert_called_once()
                self.assertIn('timeout', msmtp.call_args.kwargs)
                self.assertEqual(msmtp.call_args.kwargs['timeout'], rndval)

    def test_email_delivery_rejects_invalid_timeout(self):
        """Invalid timeouts are replaced with default"""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
            with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
                # use random number to avoid inadvertently matching default value
                for tval in ['-1', '', 'asd']:
                    mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_TIMEOUT': tval }.get(k, os.getenv(k, v))
                    e.send()
                    msmtp.assert_called_once()
                    self.assertIn('timeout', msmtp.call_args.kwargs)
                    self.assertEqual(msmtp.call_args.kwargs['timeout'], 30)
                    msmtp.reset_mock()

    def test_email_delivery_tls(self):
        """When TATTLER_SMTP_TLS envvar is given, smtp().starttls() is called upon send()"""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
            with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
                mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_TLS': 'yes' }.get(k, os.getenv(k, v))
                e.send()
                msmtp.return_value.starttls.assert_called()

    def test_email_delivery_smtpauth(self):
        """When TATTLER_SMTP_AUTH envvar is given, smtp().login() is called with the credentials it indicates."""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
            with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
                mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_AUTH': 'username:password' }.get(k, os.getenv(k, v))
                e.send()
                msmtp().login.assert_called_with('username', 'password')

    def test_email_sender_configuration(self):
        """TATTLER_EMAIL_SENDER controls email From, and gets normalized"""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_EMAIL_SENDER': None}.get(x, os.getenv(x, y))
                e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
                e.send()
                msmtp.return_value.sendmail.assert_called()
                self.assertTrue(msmtp.return_value.sendmail.call_args[0][0].strip())
                mgetenv.reset_mock()
                msmtp.reset_mock()
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_EMAIL_SENDER': 'vALId@email.addr    '}.get(x, os.getenv(x, y))
                e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
                e.send()
                msmtp.return_value.sendmail.assert_called()
                self.assertEqual('valid@email.addr', msmtp.return_value.sendmail.call_args[0][0])

    def test_get_smtp_server(self):
        """TATTLER_SMTP_ADDRESS supports formats ip4:port [ip6]:port and variants without port"""
        self.assertEqual(('127.0.0.1', 30), get_smtp_server('127.0.0.1:30'))
        self.assertEqual(('127.0.0.1', 25), get_smtp_server('127.0.0.1'))
        self.assertEqual(('a::b', 30), get_smtp_server('[a::b]:30'))
        self.assertEqual(('a::b', 25), get_smtp_server('[a::b]'))
        self.assertEqual(('a.b.c.d', 25), get_smtp_server('a.b.c.d'))
        self.assertEqual(('a.b.c.d', 30), get_smtp_server('a.b.c.d:30'))

    def test_send_raises_if_smtp_connectionreset(self):
        """send() raises ConnectionRefusedError if smtp fails to connect to"""
        with mock.patch('tattler.server.sendable.vector_email.smtplib') as msmtp:
            with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
                with mock.patch('tattler.server.sendable.vector_email.log') as mlog:
                    mgetenv.side_effect = lambda x, y=None: {'TATTLER_SMTP_ADDRESS': '4.3.2.1:98'}.get(x, os.getenv(x, y))
                    msmtp.SMTP.side_effect = ConnectionRefusedError
                    e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
                    with self.assertRaises(ConnectionRefusedError) as err:
                        e.send()
                    msmtp.SMTP.assert_called()
                    mlog.error.assert_called()
                    self.assertIn('4.3.2.1', mlog.error.call_args.args)
                    self.assertIn(98, mlog.error.call_args.args)

    def test_validate_configuration(self):
        """validate_configuration() raises iff any setting is invalid"""
        with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
            # emails
            for email_envvar in ['TATTLER_SUPERVISOR_RECIPIENT_EMAIL', 'TATTLER_DEBUG_RECIPIENT_EMAIL', 'TATTLER_EMAIL_SENDER']:
                mgetenv.side_effect = lambda x, y=None: {email_envvar: ' vALId@email.addr  '}.get(x, os.getenv(x, y))
                EmailSendable.validate_configuration()
                mgetenv.side_effect = lambda x, y=None: {email_envvar: 'in vALId@email.addr'}.get(x, os.getenv(x, y))
                with self.assertRaises(ValueError, msg=f"validate_configuration() does not raise upon invalid setting {email_envvar}"):
                    EmailSendable.validate_configuration()
                mgetenv.reset_mock()
            # smtp address
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_SMTP_ADDRESS': '1.2.3.4'}.get(x, os.getenv(x, y))
            EmailSendable.validate_configuration()
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_SMTP_ADDRESS': 'a 1.2.3.4'}.get(x, os.getenv(x, y))
            with self.assertRaises(ValueError, msg="validate_configuration() does not raise upon invalid setting 'TATTLER_SMTP_ADDRESS'"):
                EmailSendable.validate_configuration()

    def test_plain_email_with_non_ascii_characters(self):
        """support sending plaintext emails which contain non-ascii characters"""
        with mock.patch('tattler.server.sendable.vector_email.vector_sendable.getenv') as mgetenv:
            with mock.patch('tattler.server.sendable.vector_email.smtplib') as msmtp:
                mgetenv.side_effect = lambda x, y=None: {}.get(x, os.getenv(x, y))
                e = EmailSendable('event3_non_ascii', data_recipients['email'], template_base=tbase_path)
                e.send({})
                msmtp.SMTP.return_value.sendmail.assert_called()
                smtp_content = msmtp.SMTP.return_value.sendmail.call_args.args[2]
                self.assertTrue(all(ord(x) < 128 for x in smtp_content), msg="Attempts to send non-ascii content to SMTP, which requires ASCII")

if __name__ == '__main__':
    unittest.main()             # pragma: no cover
