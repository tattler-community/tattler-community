"""Tests for command-line interface to tattler client"""

import unittest
from unittest import mock
import sys

from tattler.client.tattler_py.tattler_cmd import main

class CmdLineTest(unittest.TestCase):
    """Tests for command line interface of tattler client"""

    def test_main_rejects_unknown_arguments(self):
        """Main rejects unknown arguments"""
        with mock.patch('tattler.client.tattler_py.tattler_cmd.sys') as msys:
            with self.assertRaises(SystemExit) as err:
                msys.argv = ['tattler_notify', '1', 'myscope', 'myevent', 'foo']
                main()

    def test_main_rejects_invalid_argument_values(self):
        """Main rejects unknown arguments"""
        with mock.patch('tattler.client.tattler_py.tattler_cmd.sys') as msys:
            msys.argv = ['tattler_notify', '1', 'myscope', 'myevent', '-m', 'foo']
            with self.assertRaises(SystemExit) as err:
                main()
            with self.assertRaises(SystemExit) as err:
                msys.argv = ['tattler_notify', '1', 'myscope', 'myevent', '-p', 'strval']
                main()
            with self.assertRaises(SystemExit) as err:
                msys.argv = ['tattler_notify', '1', 'myscope', 'myevent', 'context without name']
                main()
            with self.assertRaises(SystemExit) as err:
                msys.argv = ['tattler_notify', '1', 'myscope', 'myevent', '=context with empty name']
                main()
    
    def test_short_params_passed_through(self):
        """Cmdline short params are passed through to send_notification"""
        with mock.patch('tattler.client.tattler_py.tattler_cmd.sys') as msys:
            with mock.patch('tattler.client.tattler_py.tattler_cmd.send_notification') as msnot:
                msys.argv = ['tattler_notify', '1', 'myscope', 'myevent', 'foo=bar', 'x=var', '-v', 'email,sms', '-s', '3.4.5.6:321', '-m', 'staging', '-p', '2']
                msnot.return_value = True, 'asd'
                main()
                msnot.assert_called_once()
                msnot.assert_called_with('myscope', 'myevent', '1', {'foo': 'bar', 'x': 'var'}, vectors=['email', 'sms'], mode='staging', priority=2, srv_addr='3.4.5.6', srv_port=321)

    def test_long_params_passed_through(self):
        """Cmdline short params are passed through to send_notification"""
        with mock.patch('tattler.client.tattler_py.tattler_cmd.sys') as msys:
            with mock.patch('tattler.client.tattler_py.tattler_cmd.send_notification') as msnot:
                msys.argv = ['tattler_notify', '1', 'myscope', 'myevent', 'foo=bar', 'x=var', '--vectors', 'email,sms', '--server', '3.4.5.6:321', '--mode', 'staging', '--priority', '2']
                msnot.return_value = True, 'asd'
                main()
                msnot.assert_called_once()
                msnot.assert_called_with('myscope', 'myevent', '1', {'foo': 'bar', 'x': 'var'}, vectors=['email', 'sms'], mode='staging', priority=2, srv_addr='3.4.5.6', srv_port=321)
    
    def test_nonzero_exit_code_if_delivery_fails(self):
        """Cmd exists non-zero if notification request fails to send"""
        with mock.patch('tattler.client.tattler_py.tattler_cmd.sys') as msys:
            with mock.patch('tattler.client.tattler_py.tattler_cmd.send_notification') as msnot:
                msys.argv = ['tattler_notify', '1', 'myscope', 'myevent']
                msys.exit.side_effect = sys.exit
                # msnot.return_value = True, 'asd'
                # main()
                # msnot.reset_mock()
                msnot.return_value = False, 'asd'
                with self.assertRaises(SystemExit) as err:
                    main()
                self.assertEqual(err.exception.code, 1)