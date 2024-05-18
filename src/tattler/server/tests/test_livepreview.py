"""Test cases for livepreview"""

import unittest
import tempfile
import threading
import shutil
import time
from typing import Optional
from pathlib import Path
from unittest import mock

import jinja2

from tattler.server import tattler_livepreview

def delay_path_operation(fpath: Path, wait_time: float, operation: str, content: Optional[str]=None):
    """Return a function which changes a file by setting some given content after a set interval"""
    def f():
        time.sleep(wait_time)
        if operation == 'change':
            fpath.parent.mkdir(parents=True, exist_ok=True)
            print(f"Updating file {fpath}")
            fpath.write_text(content)
        elif operation == 'remove':
            if fpath.is_dir():
                print(f"Removing directory {fpath}")
                shutil.rmtree(fpath, ignore_errors=True)
    return f

class LivepreviewTest(unittest.TestCase):
    """Test cases for Live preview module"""
    def setUp(self):
        self.templates_good = Path(__file__).parent / 'fixtures' / 'livepreview' / 'templates'
        self.templates_empty = Path(__file__).parent / 'fixtures' / 'livepreview' / 'empty_templates'
        self.templates_bad = Path(__file__).parent / 'fixtures' / 'livepreview' / 'invalid_templates'
        self.templates_ctx = Path(__file__).parent / 'fixtures' / 'livepreview' / 'templates_with_context'

    def test_empty_templates_exit(self):
        """running with empty templates directory returns an error"""
        with mock.patch('tattler.server.tattler_livepreview.log') as mlog:
            with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                    with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                        margs.return_value = ['tattler_livepreview', self.templates_empty]
                        mpubinput.side_effect = KeyboardInterrupt()
                        mprivinput.side_effect = KeyboardInterrupt()
                        res = tattler_livepreview.main()
                        self.assertEqual(1, res)
                        self.assertIn("not a valid template base", mlog.error.call_args.args[0])

    def test_invalid_templates_raises(self):
        """running with invalid templates directory raises ValueError"""
        with mock.patch('tattler.server.tattler_livepreview.load_config'):
            with mock.patch('tattler.server.tattler_livepreview.get_input') as minput:
                with mock.patch('tattler.server.tattler_livepreview.send_notification'):
                    with self.assertRaises(ValueError) as err:
                        tattler_livepreview.monitor_fire(self.templates_bad)
                    self.assertIn('No template files', str(err.exception))

    def test_inexistent_template_base_raises(self):
        """running with inexistent templates directory returns failure"""
        with mock.patch('tattler.server.tattler_livepreview.log') as mlog:
            with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                margs.return_value = ['tattler_livepreview', self.templates_bad / "afkajshdfkjahsdf"]
                res = tattler_livepreview.main()
                self.assertEqual(1, res)
                self.assertIn('template base', mlog.error.call_args.args[0])

    def test_notified_when_changed(self):
        """send_notification() is called when a template file is changed"""
        with mock.patch('tattler.server.tattler_livepreview.load_config'):
            with mock.patch('tattler.server.tattler_livepreview.get_input') as minput:
                with mock.patch('tattler.server.tattler_livepreview.send_notification'):
                    with self.assertRaises(ValueError) as err:
                        tattler_livepreview.monitor_fire(self.templates_bad)
                    self.assertIn('No template files found', str(err.exception))

    def test_invalid_template_base(self):
        """cmdline fails if given template base path being a file"""
        with mock.patch('tattler.server.tattler_livepreview.send_notification'):
            with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
                with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                    margs.return_value = ['tattler_livepreview', self.templates_bad / 'email' / 'subject.txt']
                    msetenv.return_value = None
                    res = tattler_livepreview.main()
                    self.assertEqual(1, res)

    def test_private_data_obfuscated(self):
        """private config variables are stored in obfuscated form"""
        with mock.patch('tattler.server.tattler_livepreview.send_notification'):
            with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
                with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                    with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                        with mock.patch('tattler.server.tattler_livepreview.monitor_fire') as mmonitor:
                            with mock.patch('tattler.server.tattler_livepreview.get_conf_path') as mgetconf:
                                with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                                    margs.return_value = ['tattler_livepreview', self.templates_good]
                                    confpath = Path(tempfile.gettempdir()) / 'tattler_livepreview_test'
                                    confpath.mkdir(exist_ok=True)
                                    mgetconf.return_value = confpath
                                    mmonitor.side_effect = KeyboardInterrupt()
                                    msetenv.return_value = None
                                    mpubinput.side_effect = [ 'recipient@email.com', '', 'mail.srv.com:25' ]
                                    mprivinput.getpass.return_value = 'privdata817634518'
                                    res = tattler_livepreview.main()
                                    self.assertEqual(0, res)
                                    self.assertEqual(1, mmonitor.call_count)
                                    content = (confpath / 'TATTLER_SMTP_ADDRESS').read_text().strip()
                                    self.assertIn('mail.srv.com:25', content)
                                    content = (confpath / 'TATTLER_SMTP_AUTH').read_text().strip()
                                    self.assertTrue(content.strip())
                                    self.assertNotIn(mprivinput.getpass.return_value, content)

    def test_assisted_gmail_smtp_setup(self):
        """configuration recognizes 'gmail' as special SMTP service"""
        with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
            with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                    with mock.patch('tattler.server.tattler_livepreview.monitor_fire') as mmonitor:
                        with mock.patch('tattler.server.tattler_livepreview.get_conf_path') as mgetconf:
                            with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                                margs.return_value = ['tattler_livepreview', self.templates_good]
                                confpath = Path(tempfile.mkdtemp())
                                mgetconf.return_value = confpath
                                mmonitor.side_effect = KeyboardInterrupt()
                                msetenv.return_value = None
                                mpubinput.side_effect = [ 'recipient@email.com', '', 'gmail' ]
                                mprivinput.getpass.return_value = 'privdata817634518'
                                res = tattler_livepreview.main()
                                self.assertEqual(0, res)
                                self.assertEqual(1, mmonitor.call_count)
                                content = (confpath / 'TATTLER_SMTP_ADDRESS').read_text().strip()
                                self.assertIn('smtp.gmail.com', content)
                                shutil.rmtree(confpath)

    def test_configuration_values_persisted(self):
        """default values for subsequent runs take values from previous run"""
        with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
            with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                    with mock.patch('tattler.server.tattler_livepreview.monitor_fire') as mmonitor:
                        with mock.patch('tattler.server.tattler_livepreview.get_conf_path') as mgetconf:
                            with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                                margs.return_value = ['tattler_livepreview', self.templates_good]
                                confpath = Path(tempfile.mkdtemp())
                                mgetconf.return_value = confpath
                                mmonitor.side_effect = KeyboardInterrupt()
                                msetenv.return_value = None
                                # first run
                                mpubinput.side_effect = [ 'foobar@email.com', 'sender@foo.com', 'mail.g.com:465' ]
                                mprivinput.getpass.return_value = 'privdata817634518'
                                res = tattler_livepreview.main()
                                self.assertEqual(0, res)
                                # second run
                                mpubinput.side_effect = [ '', '', '' ]
                                mprivinput.getpass.return_value = ''
                                res = tattler_livepreview.main()
                                self.assertEqual(0, res)
                                content = (confpath / 'EMAIL').read_text().strip()
                                self.assertIn('foobar@email.com', content)
                                content = (confpath / 'TATTLER_EMAIL_SENDER').read_text().strip()
                                self.assertIn('sender@foo.com', content)
                                content = (confpath / 'TATTLER_SMTP_ADDRESS').read_text().strip()
                                self.assertIn('mail.g.com:465', content)
                                content = (confpath / 'TATTLER_SMTP_AUTH').read_text().strip()
                                self.assertTrue(content)
                                shutil.rmtree(confpath)

    def test_main_fails_without_templates_argument(self):
        """main() fails unless provided path to templates"""
        with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
            margs.return_value = ['tattler_livepreview', ]
            res = tattler_livepreview.main()
            self.assertNotEqual(0, res)

    def test_detects_newly_added_email_templates(self):
        """send_notification() called when an email template is added altogether"""
        with mock.patch('tattler.server.tattler_livepreview.send_notification') as msend:
            with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
                with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                    with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                        with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                            msetenv.return_value = None
                            mpubinput.side_effect = [ 'recipient@email.com', 'src@gmail.com', 'mail.srv.com:25' ]
                            mprivinput.getpass.return_value = 'privdata' + str(time.time())
                            duplicate_path = Path(tempfile.mkdtemp())
                            shutil.copytree(self.templates_good, duplicate_path, dirs_exist_ok=True)
                            margs.return_value = ['tattler_livepreview', duplicate_path]
                            for fpath, content in {
                                duplicate_path / 'some_scope' / 'new_event' / 'email' / 'subject.txt': 'foo',
                                duplicate_path / 'some_scope' / 'new_event' / 'email' / 'body.txt': 'bar',
                                duplicate_path / 'some_scope' / 'new_event' / 'context.json': '{"a": 2}'
                            }.items():
                                threading.Thread(target=delay_path_operation(fpath, 0.3, 'change', content)).start()
                            threading.Thread(target=delay_path_operation(duplicate_path, 1, 'remove')).start()
                            res = tattler_livepreview.main()
                            self.assertEqual(1, res)
                            self.assertEqual(1, msend.call_count)
                            self.assertEqual('new_event', msend.call_args.args[1])
                            self.assertEqual({'a': 2}, msend.call_args.args[3])

    def test_notification_triggered_upon_changed_file(self):
        """send_notification() called when an email template is modified"""
        with mock.patch('tattler.server.tattler_livepreview.send_notification') as msend:
            with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
                with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                    with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                        with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                            msend.side_effect = KeyboardInterrupt()
                            msetenv.return_value = None
                            mpubinput.side_effect = [ 'recipient@email.com', 'src@gmail.com', 'mail.srv.com:25' ]
                            mprivinput.getpass.return_value = 'privdata' + str(time.time())
                            target_file = self.templates_good / 'some_scope' / 'some_other_event' / 'email' / 'body.txt'
                            wthread = threading.Thread(target=delay_path_operation(target_file, 0.3, 'change', 'newcontent'))
                            wthread.start()
                            margs.return_value = ['tattler_livepreview', self.templates_good]
                            res = tattler_livepreview.main()
                            self.assertEqual(0, res)
                            self.assertEqual(1, msend.call_count)
                            self.assertEqual('email', msend.call_args.args[0])
                            self.assertEqual('some_other_event', msend.call_args.args[1])
                            self.assertEqual(['recipient@email.com'], msend.call_args.args[2])

    def test_notification_exit_disappeared_folder(self):
        """exit with failure if the template folder vanished called when an email template is modified"""
        with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
            with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                    with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                        msetenv.return_value = None
                        mpubinput.side_effect = [ 'recipient@email.com', 'src@gmail.com', 'mail.srv.com:25' ]
                        mprivinput.getpass.return_value = 'privdata' + str(time.time())
                        duplicate_path = Path(tempfile.mkdtemp())
                        shutil.copytree(self.templates_good, duplicate_path, dirs_exist_ok=True)
                        wthread = threading.Thread(target=delay_path_operation(duplicate_path, 0.3, 'remove', None))
                        wthread.start()
                        margs.return_value = ['tattler_livepreview', duplicate_path]
                        res = tattler_livepreview.main()
                        self.assertEqual(1, res)

    def test_notification_exit_no_more_events(self):
        """exit with failure if all email templates disappear from the template folder"""
        with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
            with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                    with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                        msetenv.return_value = None
                        mpubinput.side_effect = [ 'recipient@email.com', 'src@gmail.com', 'mail.srv.com:25' ]
                        mprivinput.getpass.return_value = 'privdata' + str(time.time())
                        duplicate_path = Path(tempfile.mkdtemp())
                        shutil.copytree(self.templates_good, duplicate_path, dirs_exist_ok=True)
                        margs.return_value = ['tattler_livepreview', duplicate_path]
                        for remfile in list(duplicate_path.glob('**/email')):
                            thr = threading.Thread(target=delay_path_operation(remfile, 0.5, 'remove', None))
                            thr.start()
                        res = tattler_livepreview.main()
                        shutil.rmtree(duplicate_path)
                        self.assertEqual(1, res)

    def test_notification_valid_context_loaded(self):
        """If file context.json is present, it's passed to send_notification"""
        with mock.patch('tattler.server.tattler_livepreview.send_notification') as msend:
            with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
                with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                    with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                        with mock.patch('tattler.server.tattler_livepreview.files_changed') as mchanged:
                            with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                                msetenv.return_value = None
                                mpubinput.side_effect = [ 'recipient@email.com', 'src@gmail.com', 'mail.srv.com:25' ]
                                mprivinput.getpass.return_value = 'privdata' + str(time.time())
                                target_file = self.templates_ctx / 'myscope' / 'valid_context_event' / 'email' / 'body.txt'
                                mchanged.side_effect = [
                                    {target_file},
                                    KeyboardInterrupt()
                                    ]
                                margs.return_value = ['tattler_livepreview', self.templates_ctx]
                                res = tattler_livepreview.main()
                                self.assertEqual(0, res)
                                self.assertEqual(2, mchanged.call_count)
                                self.assertEqual(1, msend.call_count)
                                self.assertEqual('email', msend.call_args.args[0])
                                self.assertEqual('valid_context_event', msend.call_args.args[1])
                                self.assertEqual({'foo': 'bar'}, msend.call_args.args[3])

    def test_notification_invalid_context_tolerated(self):
        """If file context.json is present with invalid content, send_notification is not called"""
        with mock.patch('tattler.server.tattler_livepreview.send_notification') as msend:
            with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
                with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                    with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                        with mock.patch('tattler.server.tattler_livepreview.files_changed') as mchanged:
                            with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                                msetenv.return_value = None
                                mpubinput.side_effect = [ 'recipient@email.com', 'src@gmail.com', 'mail.srv.com:25' ]
                                mprivinput.getpass.return_value = 'privdata' + str(time.time())
                                target_file = self.templates_ctx / 'myscope' / 'malformatted_context_event' / 'email' / 'body.txt'
                                mchanged.side_effect = [
                                    {target_file},
                                    KeyboardInterrupt()
                                    ]
                                margs.return_value = ['tattler_livepreview', self.templates_ctx]
                                res = tattler_livepreview.main()
                                self.assertEqual(0, res)
                                self.assertEqual(2, mchanged.call_count)
                                self.assertEqual(0, msend.call_count)

    def test_notification_malformatted_context_tolerated(self):
        """If file context.json is present with malformatted content, send_notification is not called"""
        with mock.patch('tattler.server.tattler_livepreview.send_notification') as msend:
            with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
                with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                    with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                        with mock.patch('tattler.server.tattler_livepreview.files_changed') as mchanged:
                            with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                                msetenv.return_value = None
                                mpubinput.side_effect = [ 'recipient@email.com', 'src@gmail.com', 'mail.srv.com:25' ]
                                mprivinput.getpass.return_value = 'privdata' + str(time.time())
                                target_file = self.templates_ctx / 'myscope' / 'malformatted_context_event' / 'email' / 'body.txt'
                                mchanged.side_effect = [
                                    {target_file},
                                    KeyboardInterrupt()
                                    ]
                                margs.return_value = ['tattler_livepreview', self.templates_ctx]
                                res = tattler_livepreview.main()
                                self.assertEqual(0, res)
                                self.assertEqual(2, mchanged.call_count)
                                self.assertEqual(0, msend.call_count)

    def test_notification_wellformatted_invalid_context_tolerated(self):
        """If file context.json is present with well formatted but invalid content, send_notification is not called"""
        with mock.patch('tattler.server.tattler_livepreview.send_notification') as msend:
            with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
                with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                    with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                        with mock.patch('tattler.server.tattler_livepreview.files_changed') as mchanged:
                            with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                                msetenv.return_value = None
                                mpubinput.side_effect = [ 'recipient@email.com', 'src@gmail.com', 'mail.srv.com:25' ]
                                mprivinput.getpass.return_value = 'privdata' + str(time.time())
                                target_file = self.templates_ctx / 'myscope' / 'wellformatted_invalid_context_event' / 'email' / 'body.txt'
                                mchanged.side_effect = [
                                    {target_file},
                                    KeyboardInterrupt()
                                    ]
                                margs.return_value = ['tattler_livepreview', self.templates_ctx]
                                res = tattler_livepreview.main()
                                self.assertEqual(0, res)
                                self.assertEqual(2, mchanged.call_count)
                                self.assertEqual(0, msend.call_count)

    def test_broken_jinja_content_tolerated(self):
        """Templates whose Jinja expansion fails to not cause livepreview to return error"""
        with mock.patch('tattler.server.tattler_livepreview.send_notification') as msend:
            with mock.patch('tattler.server.tattler_livepreview.setenv') as msetenv:
                with mock.patch('tattler.server.tattler_livepreview.get_input') as mpubinput:
                    with mock.patch('tattler.server.tattler_livepreview.getpass') as mprivinput:
                        with mock.patch('tattler.server.tattler_livepreview.files_changed') as mchanged:
                            with mock.patch('tattler.server.tattler_livepreview.log') as mlog:
                                with mock.patch('tattler.server.tattler_livepreview.get_cmdline_args') as margs:
                                    margs.return_value = ['tattler_livepreview', self.templates_good]
                                    for exc in [
                                        jinja2.exceptions.UndefinedError("base_template"),
                                        jinja2.exceptions.UndefinedError("undefined variable"),
                                        jinja2.exceptions.TemplateAssertionError("Some bad stuff happened", lineno=1),
                                    ]:
                                        msend.side_effect = exc
                                        msetenv.return_value = None
                                        mpubinput.side_effect = [ 'recipient@email.com', 'src@gmail.com', 'mail.srv.com:25' ]
                                        mprivinput.getpass.return_value = 'privdata' + str(time.time())
                                        target_file = self.templates_ctx / 'myscope' / 'wellformatted_invalid_context_event' / 'email' / 'body.txt'
                                        mchanged.side_effect = [
                                            {target_file},
                                            KeyboardInterrupt()
                                            ]
                                        res = tattler_livepreview.main()
                                        self.assertEqual(0, res)
                                        self.assertEqual(1, msend.call_count)
                                        self.assertEqual(1, mlog.error.call_count)
                                        self.assertIn("Failed to load template", mlog.error.call_args.args[0])
                                        msend.reset_mock()
                                        mlog.reset_mock()


if __name__ == '__main__':
    unittest.main()
