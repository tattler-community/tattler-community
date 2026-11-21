"""SMS delivery backend for BulkGate's HTTP Simple Transactional API.

See https://www.bulkgate.com/en/docs/simple-api/simple-transactional/ .

BulkGate reports delivery status only by pushing to a pre-configured webhook, and offers
no polling facility; delivery_status() is therefore unsupported and returns no data.
"""

import json
import logging
import os
import re
import urllib.request
from typing import Iterable, Mapping, Optional, Tuple

from tattler.server.sendable import vector_sendable
from tattler.server.sendable.delivery_backend import DeliveryBackend, SendResult
from tattler.server.sendable.vector_sms import sender_kind

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)


class BulkGateBackend(DeliveryBackend):
    """Deliver SMS through BulkGate's HTTP Simple Transactional API."""

    @classmethod
    def vector(cls) -> str:
        return 'sms'

    api_url = 'https://portal.bulkgate.com/api/1.0/simple/transactional'
    timeout_s = 10

    required_settings = {
        'TOKEN': [True, lambda v: re.match(r'.+:.+', v)],
    }

    def get_auth(self) -> Tuple[str, str]:
        """Return the application credentials pair configured for authentication.

        :raise ValueError:  When the configured value is not a ':'-separated pair.

        :return:            Application ID and application token."""
        varname = self.envvar('TOKEN')
        authstr = vector_sendable.getenv(varname)
        assert authstr, f"Presence of auth config '{varname}' must be pre-validated before get_auth()"
        try:
            app_id, app_token = authstr.strip().split(':', 1)
        except ValueError as err:
            raise ValueError(f"Envvar '{varname}' is malformed: required 'application_id:application_token'.") from err
        return app_id, app_token

    def sender_params(self, sender: Optional[str]) -> Mapping[str, str]:
        """Return the request parameters selecting a sender, as either an own number or a text name.

        :param sender:      Sender ID to send as, or None to let BulkGate apply its default.

        :raise ValueError:  When the sender is neither an international number nor a valid alphanumeric name.

        :return:            Parameters to add to the request; empty if no sender is given."""
        if not sender:
            return {}
        match sender_kind(sender):
            case 'number':
                return {'sender_id': 'gOwn', 'sender_id_value': sender.removeprefix('+').removeprefix('00')}
            case 'name':
                return {'sender_id': 'gText', 'sender_id_value': sender}
        raise ValueError(f"Sender '{sender}' is neither a number in international format nor an alphanumeric name of up to 11 characters.")

    def send(self, recipients: Iterable[str], body: str, sender: Optional[str]=None, priority: Optional[int]=None) -> SendResult:
        # the Simple Transactional API takes one recipient per call
        app_id, app_token = self.get_auth()
        sender_params = self.sender_params(sender)
        msgids = {}
        for rcpt in recipients:
            params = {
                'application_id': app_id,
                'application_token': app_token,
                'number': rcpt.lstrip('+'),
                'text': body,
                'unicode': '0' if body.isascii() else '1',
                **sender_params,
            }
            req = urllib.request.Request(self.api_url, data=json.dumps(params).encode(),
                                         headers={'Content-Type': 'application/json'}, method='POST')
            log.debug("Sending SMS to '%s' via %s", rcpt, self.api_url)
            with urllib.request.urlopen(req, timeout=self.timeout_s) as f:
                res = json.loads(f.read().decode())
            if 'data' not in res:
                raise ValueError(f"BulkGate rejected message to '{rcpt}': {res.get('error', res)}")
            msgids[rcpt] = res['data']['sms_id']
        return SendResult(recipient_ids=msgids)
