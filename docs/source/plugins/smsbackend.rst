SMS backend plug-ins
====================

SMS backend plug-ins let tattler deliver SMS through a gateway it does not support out of the box.
The same interface also lets you add entirely new vectors: see `Delivering a custom vector`_.

Tattler ships with backends for `BulkSMS.com <https://www.bulksms.com>`_ and `BulkGate <https://www.bulkgate.com>`_ .
It selects backends by configuration: every backend whose settings are present and valid takes part in delivery.
Backends are grouped by the vector they declare, and failover applies within the group: an SMS delivery
only ever attempts backends declaring vector ``'sms'``. When multiple backends of a vector are configured
-- built-in or plug-in -- tattler tries them in alphabetical order of their name, and falls over to the
next when one fails to accept the message.

Writing an SMS backend plug-in
------------------------------

SMS backend plug-ins are python files that

- are placed in the :ref:`plug-in directory <configuration:TATTLER_PLUGIN_PATH>`,
- implement the interface of class :class:`DeliveryBackend <tattler.server.sendable.delivery_backend.DeliveryBackend>`.

Plug-in filenames **must** end with ``_tattler_plugin.py``; other filenames are ignored.

A minimal backend declares its vector, declares its settings in ``required_settings``, and implements
:meth:`send() <tattler.server.sendable.delivery_backend.DeliveryBackend.send>`:

.. code-block:: python

    import re
    import requests

    from tattler.server.sendable import vector_sendable
    from tattler.server.sendable.delivery_backend import DeliveryBackend, SendResult


    class AcmeBackend(DeliveryBackend):
        """Deliver SMS through ACME's HTTP API."""

        @classmethod
        def vector(cls):
            return 'sms'

        # settings are looked up as TATTLER_{NAME}_{SUFFIX}, e.g. TATTLER_ACME_TOKEN;
        # each suffix maps to [required, validator]
        required_settings = {
            'TOKEN': [True, lambda v: re.match(r'\w+', v)],
        }

        def send(self, recipients, body, sender=None, priority=None):
            msgids = {}
            for rcpt in recipients:
                resp = requests.post('https://api.acme.example/sms', json={
                    'token': vector_sendable.getenv(self.envvar('TOKEN')),
                    'to': rcpt,
                    'text': body,
                }, timeout=10)
                resp.raise_for_status()
                msgids[rcpt] = resp.json()['message_id']
            return SendResult(recipient_ids=msgids)

A few things to know:

- **Vector.** ``vector()`` tells tattler which kind of delivery this backend performs; for an SMS
  backend it must return ``'sms'``. It also determines which group the backend fails over within.
- **Naming.** The backend's name defaults to the class name, lowercased and without any ``Backend``
  suffix -- ``AcmeBackend`` becomes ``acme``. The name namespaces the backend's settings
  (``TATTLER_ACME_TOKEN``) and determines its position in the failover order.
- **Configuration is the on/off switch.** A backend is only used when all its ``required_settings``
  are present and valid. Tattler validates them when it loads the plug-in, so misconfiguration
  surfaces at startup rather than at first delivery. A backend with none of its settings provided
  is simply skipped, with an informational log line; one with settings missing or malformed is
  skipped with an error.
- **What "success" means.** Return from ``send()`` when the gateway accepted the message for
  delivery; raise on any failure, so tattler can fall over to the next configured backend.
- **Optional facilities.** Implement :meth:`cost() <tattler.server.sendable.delivery_backend.DeliveryBackend.cost>`
  if your gateway can quote a delivery before sending, and
  :meth:`delivery_status() <tattler.server.sendable.delivery_backend.DeliveryBackend.delivery_status>` if it
  supports polling for delivery reports. Both default to "no data available".

See :ref:`Deploying plug-ins <sysadmins/deploy_plugins:Deploy custom plug-ins>` for tips on deployment.

Delivering a custom vector
--------------------------

A backend may declare any name in ``vector()`` -- not just ``'sms'``. Declaring e.g. ``'signal'``
is all it takes for tattler to accept and deliver that vector:

- Clients may request the vector: ``tattler_notify -v signal ...``.
- Template designers provide content for it in the usual per-vector folder, e.g. ``my_event/signal/body.txt``.
- Your addressbook must return the recipient's address under that key, e.g. ``{'signal': '+19876543210'}``
  from :meth:`attributes() <tattler.server.pluginloader.AddressbookPlugin.attributes>`.
- The usual per-vector settings apply, e.g. ``TATTLER_SIGNAL_SENDER`` and ``TATTLER_DEBUG_RECIPIENT_SIGNAL``.

Override :meth:`validate_recipient() <tattler.server.sendable.delivery_backend.DeliveryBackend.validate_recipient>`
to declare what a valid address looks like for your vector -- return the normalized address, or raise
``ValueError``. By default any address is accepted. When multiple backends serve one vector, a recipient
is accepted if any backend accepts it, and the first accepting backend provides the normalization:

.. code-block:: python

    class SignalBackend(DeliveryBackend):
        """Deliver messages through Signal."""

        @classmethod
        def vector(cls):
            return 'signal'

        @classmethod
        def validate_recipient(cls, recipient):
            if not re.match(r'\+[1-9][0-9]+', recipient):
                raise ValueError(f"Signal recipients are phone numbers like '+19876543210', not '{recipient}'.")
            return recipient

        def send(self, recipients, body, sender=None, priority=None):
            ...

DeliveryBackend reference
--------------------------

.. autoclass:: tattler.server.sendable.delivery_backend.DeliveryBackend
    :members: vector, name, envvar, send, validate_recipient, cost, delivery_status

.. autoclass:: tattler.server.sendable.delivery_backend.SendResult

.. autoclass:: tattler.server.sendable.delivery_backend.DeliveryStatus
