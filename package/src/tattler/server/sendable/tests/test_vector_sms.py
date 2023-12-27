import unittest
import unittest.mock
import os

# test TATTLER_BULKSMS_TOKEN envvar with unacceptable format
os.environ['TATTLER_BULKSMS_TOKEN'] = '3456789'

from tattler.server.sendable.vector_sms import SMSSendable

class TestVectorSMS(unittest.TestCase):
    def test_construction(self):
        s = SMSSendable('event', ['+123456789'])
        self.assertIsNotNone(s)
    
    def test_assert_prefix_plus_zero_equivalent(self):
        sp = SMSSendable('event', ['+123456789'])
        self.assertIsNotNone(sp)
        s0 = SMSSendable('event', ['00123456789'])
        self.assertIsNotNone(s0)
        self.assertEqual(s0.recipients, sp.recipients)

    def test_invalid_recipient_rejected(self):
        with self.assertRaises(ValueError):
            s = SMSSendable('event', 'asd')
    
    def test_invalid_auth_data(self):
        with unittest.mock.patch('tattler.server.sendable.vector_sms.getenv') as mgetenv:
            with unittest.mock.patch('tattler.server.sendable.vector_sms.BulkSMS') as msms:
                mgetenv.side_effect = lambda x, y=None: {'TATTLER_BULKSMS_TOKEN': 'foobar'}.get(x, os.getenv(x, y))
                with self.assertRaises(ValueError):
                    s0 = SMSSendable('event', ['00123456789'])
                    s0.get_sms_server()

if __name__ == '__main__':
    unittest.main()
