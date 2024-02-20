import re
from typing import Optional

from tattler.server.pluginloader import AddressbookPlugin


class PassThroughAddressbookPlugin(AddressbookPlugin):
    """Use recipient ID as respective contact if it looks like one; e.g. 'foo@bar.com' for email."""

    def email(self, recipient_id: str, role: Optional[str]=None) -> Optional[str]:
        """Return recipient_id itself, if it looks like an email address."""
        if re.match(r'^[^@\s]+@([_a-zA-Z0-9-]+\.)*[_a-zA-Z0-9-]+$', recipient_id):
            return recipient_id
        return None
    
    def mobile(self, recipient_id: str, role: Optional[str]=None) -> Optional[str]:
        """Return recipient_id itself, if it looks like a mobile number."""
        if re.match(r'^(\+|00)[0-9]{5,16}$', recipient_id):
            if recipient_id.startswith('00'):
                return '+' + recipient_id[2:]
            return recipient_id
        return None
