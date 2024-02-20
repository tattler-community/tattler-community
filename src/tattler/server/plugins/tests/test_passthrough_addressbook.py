"""Tests for PassThroughAddressbookPlugin"""

import unittest

from tattler.server.plugins.passthrough_addressbook_tattler_plugin import PassThroughAddressbookPlugin

class PassThroughAddressbookPluginTest(unittest.TestCase):
    """Test cases for PassThroughAddressbookPlugin."""

    def test_email_recipient_includes_email(self):
        """Attributes for email recipient includes correct email"""
        attr = PassThroughAddressbookPlugin().attributes('foo@bar.com')
        self.assertIn('email', attr)
        self.assertEqual('foo@bar.com', attr['email'])

    def test_email_recipient_excludes_other_vectors(self):
        """Attributes for email recipient has other vectors None"""
        attr = PassThroughAddressbookPlugin().attributes('foo@bar.com')
        for vname in ['mobile', 'language']:
            self.assertIn(vname, attr)
            self.assertIsNone(attr[vname])

    def test_mobile_recipient_includes_mobile(self):
        """Attributes for mobile recipient includes correct mobile number"""
        attr = PassThroughAddressbookPlugin().attributes('+4132154399')
        self.assertIn('mobile', attr)
        self.assertEqual('+4132154399', attr['mobile'])
    
    def test_mobile_recipient_accepts_nullprefix(self):
        """mobile() accepts numbers starting with 00 and with '+'"""
        ptp = PassThroughAddressbookPlugin()
        for num in ['004132154399', '+4132154399']:
            attr = ptp.attributes(num)
            self.assertIn('mobile', attr, msg=f"PassThroughAddressbookPlugin rejects valid mobile number '{num}'")
            self.assertEqual('+4132154399', attr['mobile'], msg=f"PassThroughAddressbookPlugin mismatches valid mobile number '{num}'")

    def test_mobile_recipient_excludes_other_vectors(self):
        """Attributes for mobile recipient has other vectors None"""
        attr = PassThroughAddressbookPlugin().attributes('+4132154399')
        for vname in ['email', 'language']:
            self.assertIn(vname, attr)
            self.assertIsNone(attr[vname])

    def test_role_makes_no_difference(self):
        """Passing a role attribute does not change attributes"""
        attr_unroled = PassThroughAddressbookPlugin().attributes('foo@bar.com')
        attr_roled = PassThroughAddressbookPlugin().attributes('foo@bar.com', role='some')
        self.assertEqual(attr_roled, attr_unroled)
