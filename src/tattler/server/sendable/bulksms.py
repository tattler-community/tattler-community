import logging
import string
import json
import base64

import urllib.request
import urllib.parse

# in { 'ECONOMY', 'STANDARD', 'PREMIUM' }. See https://www.bulksms.com/pricing/sms-routing.htm
default_routing_group = 'STANDARD'

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def normalize_recipient(r):
	if any([c in string.ascii_letters for c in r]):
		# symbolic recipient, not numeric. 
		return r.strip()
	r = ''.join([d for d in r if d in string.digits])
	return '+' + r.lstrip('0')

class BulkSMS:
	api_base = 'https://api.bulksms.com/v1'
	timeout_s = 4
	routing_group = default_routing_group

	def __init__(self, token_id=None, token_secret=None, username=None, password=None, sender=None):
		if token_id is None and username is None:
			raise ValueError("Either token or username/password must be given.")
		self.login = {
			'username': username or token_id,
			'password': password or token_secret,
		}
		self.sender = None
		if sender is not None:
			self.sender = normalize_recipient(sender)

	def get_headers(self):
		astr = '%s:%s' % (self.login['username'], self.login['password'])
		return {
			'Content-Type': 'application/json',
			'Authorization': 'Basic %s' % base64.b64encode(astr.encode()).decode()
			}

	def do_send(self, url, content=b'', method='GET', js=None):
		log.debug("Sending req to: %s", url)
		headers= self.get_headers()
		log.debug(headers)
		if js is not None:
			content += json.dumps(js).encode()
		req = urllib.request.Request(url, method=method.upper(), data=content, headers=headers)
		try:
			with urllib.request.urlopen(req, timeout=self.timeout_s) as f:
				return json.loads(f.read().decode())
		except Exception as e:
			log.error("Error submitting request to %s: %s" % (url, e))
			raise

	def get_url(self, resource, params=None):
		url = self.api_base + '/' + resource.lstrip('/')
		if params is None:
			return url
		return url + '?' + urllib.parse.urlencode(params)

	def get_sender(self, sender=None):
		if sender is None:
			return self.sender
		return normalize_recipient(sender)
		
	def send(self, recipients, content, sender=None, priority=False):
		"""Send message to some recipients."""
		if isinstance(recipients, str):
			recipients = [recipients]
		recipients = [normalize_recipient(r) for r in recipients]
		params = {
			'to': recipients,
			'body': content,
			'routingGroup': "PREMIUM" if priority else self.routing_group.upper()
		}
		if sender or self.sender:
			params['from'] = normalize_recipient(sender) if sender else self.sender
		try:
			res = self.do_send(self.get_url('messages'), js=params, method='POST')
		except Exception as e:
			log.error("Message to %s failed to send: %s", recipients, e)
			raise
		log.debug("Message to %s successfully sent: %s", recipients, res)
		return [msg['submission']['id'] for msg in res]
	
	def msg_status(self, submission_id):
		"""Return raw message delivery status."""
		filter_params = {
			'type': 'SENT',
			'submission.id': submission_id
		}
		params = {
			'filter': urllib.parse.urlencode(filter_params)
		}
		return self.do_send(self.get_url('messages', params))

	def msg_delivery_status(self, submission_id):
		"""Return delivery status in {'ACCEPTED', 'SCHEDULED', 'SENT', 'DELIVERED', 'FAILED'}."""
		res = self.msg_status(submission_id)
		try:
			return res[0]['status']['type'].upper()
		except:
			raise ValueError("Unable to parse result from server: '%s'" % res)

	def msg_cost(self, submission_id):
		"""Return cost of message delivery in credits."""
		res = self.msg_status(submission_id)
		try:
			return res[0]['status']['creditCost']
		except:
			raise ValueError("Unable to parse result from server: '%s'" % res)
