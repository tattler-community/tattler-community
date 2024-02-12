import unittest
import unittest.mock
import os

# test TATTLER_BULKSMS_TOKEN envvar with unacceptable format
os.environ['TATTLER_BULKSMS_TOKEN'] = '3456789'

from tattler.server.sendable.vector_sms import SMSSendable

class TestVectorSMS(unittest.TestCase):
    def test_construction(self):
        """Constructor succeeds if valid data is passed to it"""
        s = SMSSendable('event', ['+123456789'])
        self.assertIsNotNone(s)
    
    def test_assert_prefix_plus_zero_equivalent(self):
        """Constructor accepts mobile numbers with plus or 00 prefix"""
        sp = SMSSendable('event', ['+123456789'])
        self.assertIsNotNone(sp)
        s0 = SMSSendable('event', ['00123456789'])
        self.assertIsNotNone(s0)
        self.assertEqual(s0.recipients, sp.recipients)

    def test_invalid_recipient_rejected(self):
        """SMSSendable constructor raises iff given recipient is malformed"""
        with self.assertRaises(ValueError):
            SMSSendable('event', ['asd'])
    
    def test_invalid_auth_data(self):
        """SMSSendable constructor raises iff TATTLER_BULKSMS_TOKEN malformed"""
        with unittest.mock.patch('tattler.server.sendable.vector_sms.vector_sendable.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.sendable.vector_sms.BulkSMS') as msms:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': 'foobar'}.get(x, os.getenv(x, y))
                with self.assertRaises(ValueError):
                    s0 = SMSSendable('event', ['00123456789'])
                    s0.get_sms_server()

    def test_validate_configuration_token(self):
        """validate_configuration() fails iff settings missing or malformed"""
        with unittest.mock.patch('tattler.server.sendable.vector_sms.vector_sendable.getenv') as mgetenv:
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': None}.get(x, os.getenv(x, y))
            with self.assertRaises(ValueError) as err:
                SMSSendable.validate_configuration()
            self.assertIn('TATTLER_BULKSMS_TOKEN', str(err.exception))
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': 'invalid string; 123'}.get(x, os.getenv(x, y))
            with self.assertRaises(ValueError) as err:
                SMSSendable.validate_configuration()
            self.assertIn('TATTLER_BULKSMS_TOKEN', str(err.exception))
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '123:afadad121435'}.get(x, os.getenv(x, y))
            SMSSendable.validate_configuration()
            
    def test_validate_configuration_sender(self):
        """validate_configuration() fails iff settings missing or malformed"""
        with unittest.mock.patch('tattler.server.sendable.vector_sms.vector_sendable.getenv') as mgetenv:
            # TATTLER_SMS_SENDER not provided => ok
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas'}.get(x, os.getenv(x, y))
            SMSSendable.validate_configuration()
            # TATTLER_SMS_SENDER provided, malformed => error
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas', 'TATTLER_SMS_SENDER': 'asd'}.get(x, os.getenv(x, y))
            with self.assertRaises(ValueError) as err:
                SMSSendable.validate_configuration()
            self.assertIn('TATTLER_SMS_SENDER', str(err.exception))
            # TATTLER_SMS_SENDER provided, well-formed => ok
            mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': '12:aas', 'TATTLER_SMS_SENDER': '+12345'}.get(x, os.getenv(x, y))
            SMSSendable.validate_configuration()


if __name__ == '__main__':
    unittest.main()
