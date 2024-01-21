import unittest
from unittest import mock
import os

from pathlib import Path

from tattler.server.sendable.vector_email import EmailSendable, get_smtp_server

data_recipients = {
    'email': ['support@test123.com'],
    'sms': ['+11234567898', '00417689876']
}

# template fixtures generic to multiple vectors
tbase_standard_path = Path(__file__).parent.joinpath('fixtures', 'templates')
# template fixtures specific to this vector
tbase_path = Path(__file__).parent.joinpath('fixtures', 'templates_with_base')

class TestVectorEmail(unittest.TestCase):

    def test_content_with_base(self):
        """Sendable can be constructed and content() called"""
        s = EmailSendable('event1', ['foo@bar.com'], template_base=tbase_path)
        s.content(context={})

    def test_send_with_ipv6(self):
        """IPv6 address for SMTP SERVER is supported"""
        s = EmailSendable('event1', ['foo@bar.com'], template_base=tbase_path)
        srvaddr_want = '12:34::1'
        with mock.patch('tattler.server.sendable.vector_email.getenv') as mgetenv:
            mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_ADDRESS': f"[{srvaddr_want}]:25" }.get(k, os.getenv(k, v))
            with mock.patch('tattler.server.sendable.vector_email.smtplib') as msmtp:
                s.send()
                self.assertTrue(msmtp.SMTP.mock_calls)
                self.assertEqual(msmtp.SMTP.call_args.args[0], srvaddr_want)
    
    def test_send_invalid_server(self):
        """Passing an invalid SMTP server address raises ValueError"""
        s = EmailSendable('event1', ['foo@bar.com'], template_base=tbase_path)
        with mock.patch('tattler.server.sendable.vector_email.getenv') as mgetenv:
            mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_ADDRESS': "['12:34::1']:25" }.get(k, os.getenv(k, v))
            with mock.patch('tattler.server.sendable.vector_email.smtplib') as msmtp:
                with self.assertRaises(ValueError):
                    s.send()

    def test_send_priority_numeric(self):
        """When a valid (integer) priority is provided, it's applied into the headers of the email delivered"""
        s = EmailSendable('event1', ['foo@bar.com'], template_base=tbase_path)
        with mock.patch('tattler.server.sendable.vector_email.getenv') as mgetenv:
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
        with mock.patch('tattler.server.sendable.vector_email.getenv') as mgetenv:
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
        with mock.patch('tattler.server.sendable.vector_email.getenv') as mgetenv:
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

    def test_email_html(self):
        """HTML email contains text/html part"""
        e = EmailSendable('event_with_email_and_sms', data_recipients['email'], template_base=tbase_standard_path)
        self.assertIn('text/html', e.content(context={'one': '#1234#'}))

    def test_email_send_triggers_delivery(self):
        """send() calls smtp().sendmail()"""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
            e.send()
            msmtp.assert_called()
            msmtp().sendmail.assert_called()
            self.assertFalse(msmtp().starttls.call_args)
    
    def test_email_delivery_tls(self):
        """When TATTLER_SMTP_TLS envvar is given, smtp().starttls() is called upon send()"""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
            with mock.patch('tattler.server.sendable.vector_email.getenv') as mgetenv:
                mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_TLS': 'yes' }.get(k, os.getenv(k, v))
                e.send()
                msmtp().starttls.assert_called()

    def test_email_delivery_smtpauth(self):
        """When TATTLER_SMTP_AUTH envvar is given, smtp().login() is called with the credentials it indicates."""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            e = EmailSendable('event_with_email_plain', data_recipients['email'], template_base=tbase_standard_path)
            with mock.patch('tattler.server.sendable.vector_email.getenv') as mgetenv:
                mgetenv.side_effect = lambda k,v=None: { 'TATTLER_SMTP_AUTH': 'username:password' }.get(k, os.getenv(k, v))
                e.send()
                msmtp().login.assert_called_with('username', 'password')

    def test_email_sender_configuration(self):
        """TATTLER_EMAIL_SENDER controls email From, and gets normalized"""
        with mock.patch('tattler.server.sendable.vector_email.smtplib.SMTP') as msmtp:
            with mock.patch('tattler.server.sendable.vector_email.getenv') as mgetenv:
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


if __name__ == '__main__':
    unittest.main()