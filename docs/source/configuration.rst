.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

Configuration
=============

``tattler_server`` is configured via environment variables.


.. _configuration_template_base:

TATTLER_TEMPLATE_BASE
---------------------

The path where tattler should find :ref:`notification events <keyconcepts/events:notification events>`, or more specifically notification
scopes which then include templates for notification events.


LOG_LEVEL
---------

Only log events with a severity equal or higher than this.

Supported values: ``debug``, ``info``, ``warning``, ``error``.


TATTLER_SMS_SENDER
------------------

Mobile number to use as sender for notification SMSes, e.g. ``+16315551234``.

If unset, tattler will let the delivery network apply the default source number.

You may provide multiple numbers, separated by a comma. For example: ``+16315551234,+4478456325,+3389453812``.
This allows you to reach notification recipients in different countries using a local number -- for example
to allow them to reply locally or to comply with regulations.

If you do provide multiple SMS sender numbers, tattler will use the one sharing the longest
prefix with the notification recipient's number.
If none of the numbers has a common prefix with the recipient's number, tattler defaults to
the first value in the list.


TATTLER_EMAIL_SENDER
--------------------

Email address to use as sender for notification emails.

If unset, tattler lets the SMTP library determine the default address, which usually looks like ``running_username@hostname``.


TATTLER_MASTER_MODE
-------------------

"Master" mode to operate with. This mode limits the mode requested in every incoming notification request.

See :ref:`notification modes <keyconcepts/mode:notification mode>`.


TATTLER_SUPERVISOR_RECIPIENT_*
------------------------------

Recipient address to copy notifications to when sent in ``staging`` :ref:`notification mode <keyconcepts/mode:notification mode>`.

Notifications are sent to the actual recipient, and *copied* to the supervisor recipient.

This variable should be set for every desired vector:

* TATTLER_SUPERVISOR_RECIPIENT_EMAIL
* TATTLER_SUPERVISOR_RECIPIENT_SMS


TATTLER_DEBUG_RECIPIENT_*
-------------------------

Recipient address to send notifications to when sent in ``debug`` :ref:`notification mode <keyconcepts/mode:notification mode>`.

This variable should be set for every desired vector:

* TATTLER_DEBUG_RECIPIENT_EMAIL
* TATTLER_DEBUG_RECIPIENT_SMS


TATTLER_BLACKLIST_PATH
----------------------

Path to a file to be used to store blacklist: a list of recipient addresses that tattler will skip sending to if asked.

Blacklists are useful for a variety of scenarios, including omitting delivery to addresses that are known to bounce,
especially when such deliveries come at a monetary or reputational cost, such as in the case of delivery through services
like Amazon SES.

This file is read-only for tattler. Tattler looks up content anew at every delivery attempt.

If the file is missing, inaccessible or unreadable, the entry is considered valid (not blacklisted).

This is a text file containing one blacklisted entry per line. Entries of different
:ref:`vectors <keyconcepts/vectors:notification vectors>` can be mixed in one same blacklist file.


TATTLER_BULKSMS_TOKEN
---------------------

The token to use to deliver SMS notifications via `BulkSMS.com <https://www.bulksms.com>`_ .

The token is formatted as a pair of (user_id, secret) separated by a colon, i.e. ``user_id:secret``.


TATTLER_SMTP_ADDRESS
--------------------

The address and port number of the host to use for SMTP delivery, formatted as:

- For IPv4: ``ip_address:port_number`` or simply ``ip_address`` to default on port 25. E.g. ``192.168.0.1:26``
- For IPv6: ``[ip6_address]:port_number`` or simply ``[ip6_address]`` to default on port 25. E.g. ``[2a00:1450:400a:802::2005]:25``
- For hostname: ``hostname:port_number`` or simply ``hostname`` to default on port 25. E.g. ``smtp.gmail.com:465``

**Nota bene**: Tattler will use the port number to decide whether to connect in plain TCP or TLS. Well-known SMTP-TLS ports
are: 465, 587.

Default: ``127.0.0.1:25``

TATTLER_SMTP_TIMEOUT
--------------------

Wait on SMTP server for up to this many seconds before failing. It must be a positive integer.

Default: ``30``


TATTLER_SMTP_TLS
----------------

Set to any non-empty value to cause SMTP delivery to occur over a STARTTLS session.


TATTLER_SMTP_AUTH
-----------------

Credentials for SMTP AUTH, if the `TATTLER_SMTP_ADDRESS`_ requires one.

Set to a (username, password) pair, divided by a colon, like ``my@email.com:My_PassWord``.


TATTLER_PLUGIN_PATH
-------------------

Path where tattler should search for available plug-ins.


TATTLER_LISTEN_ADDRESS
----------------------

IP address and port number to listen on for requests from clients.

Nota bene: hostnames are not supported.

Default: ``127.0.0.1:11503``


TATTLER_TEMPLATE_TYPE
---------------------

Name of the template processor to use.

Default: ``jinja``


TATTLER_WHATSAPP_SENDER
-----------------------

.. note:: This feature is only available in Tattler's `enterprise edition <https://tattler.dev#enterprise>`_.

The "Phone number ID" to use as source when sending messages via WhatsApp, e.g ``263465548029294``.

.. caution:: This is not a phone number!!

    This is the numeric identifier which Meta uses to refer to the actual phone number. Find this within you "Meta for developers" account,
    selecting the App and then its WhatsApp settings.

Only required if you actually send messages via WhatsApp.

Refer to Meta's documentation on how to set yourself up to
`send messages to WhatsApp <https://developers.facebook.com/docs/whatsapp/cloud-api/get-started#get-access-token>`_.

Default: *none*


TATTLER_WHATSAPP_ACCESS_TOKEN
-----------------------------

.. note:: This feature is only available in Tattler's `enterprise edition <https://tattler.dev#enterprise>`_.

Access token to deliver messages via WhatsApp.

Only required if you actually send messages via WhatsApp.

Refer to Meta's documentation on how to set yourself up to
`send messages to WhatsApp <https://developers.facebook.com/docs/whatsapp/cloud-api/get-started#get-access-token>`_.

Default: *none*


TATTLER_TELEGRAM_BOT_TOKEN
--------------------------

.. note:: This feature is only available in Tattler's `enterprise edition <https://tattler.dev#enterprise>`_.

Token for the Bot used to send messages via Telegram.

Only required if you actually send messages via Telegram.

Refer to Telegram's documentation on how to `obtain a Bot token <https://core.telegram.org/bots/tutorial#obtain-your-bot-token>`_.
