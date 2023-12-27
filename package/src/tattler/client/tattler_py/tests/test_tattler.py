import unittest
from unittest import mock

import os
import urllib
import shutil
from datetime import datetime

from tattler.client.tattler_py.tattler_client import TattlerClient


class TattlerClientTest(unittest.TestCase):
    port = 11503

    def test_dead_letter_store_triggered_upon_notification_failure(self):
        n = TattlerClient('test_scope', '127.0.0.1', self.port)
        with mock.patch('tattler.client.tattler_py.tattler_client.TattlerClient.do_send') as mdosend:
            mdosend.side_effect = urllib.error.URLError("Cannot connect")
            want_time = datetime(2022, 6, 9, 18, 44, 15, 157049)
            want_context = {
                'datetime': want_time,
                'date': want_time.date(),
                'set': {3, 2, 1}
                }
            # cleanup any existing deadletter path, to ensure it's created
            dlpath = os.path.join(os.sep, 'tmp', 'tattler_deadletter')
            os.environ['TATTLER_DEADLETTER_PATH'] = dlpath
            try:
                assert 'tmp' in dlpath
                shutil.rmtree(dlpath)
            except OSError:
                pass
            res = n.send(['email'], 'test_event', 1, context=want_context)
            self.assertFalse(res)
            # deadletter folder exists
            self.assertTrue(os.path.exists(dlpath))
            # there's one file in it
            deadletters = os.listdir(dlpath)
            self.assertTrue(deadletters)
            self.assertEqual(1, len(deadletters))
            # filename contains scope name
            self.assertTrue(all(['test_scope' in x for x in deadletters]))
            # filename contains event name
            self.assertTrue(all(['test_event' in x for x in deadletters]))
            # filename contains recipient
            self.assertTrue(all(['_1' in x for x in deadletters]))
            shutil.rmtree(dlpath)
            del os.environ['TATTLER_DEADLETTER_PATH']