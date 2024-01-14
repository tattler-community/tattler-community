.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

Key concepts
============

Notification vectors
--------------------

tattler supports delivering notifications over email and SMS. Each of these is called a "vector".

Notification vectors determine:

* the recipient address required (email? mobile number?)
* the content to notify (short, long? supports attachments?)

and more.

A notification may be delivered to one or multiple vectors, as determined by 3 factors:

* Content availability: is content for that vector available for the `event <notification events>`_ we are trying to send?
* Recipient availability: is a valid address available for the given vector (e.g. email address, phone number) for the requested user?
* Explicit request: has the client application asked explicitly to restrict delivery to a subset of the available vectors?

.. note:: Tattler enterprise edition
    Additional notification vectors exist in tattler's enterprise edition:

    - WhatsApp -- requires a mobile number as recipient address.
    - Telegram -- requires a *telegram ID* as recipient address.


Content availability
^^^^^^^^^^^^^^^^^^^^

When a request arrives to deliver an `event <notification events>`_, tattler checks what vectors
are available for it.

Your template designer defines which events are available for each event, by placing respective files in the template structure:

.. code-block:: bash

    templates_base/
    └── mywebapp/
        └── password_changed/
            ├── email/
            │   ├── body_html
            │   ├── body_plain
            │   └── subject
            └── sms

See docs for :doc:`templatedesigners`.


Recipient availability
^^^^^^^^^^^^^^^^^^^^^^

In trivial deployments, your client applications give tattler the actual address of the recipient with each request.

This only allows for delivering the notification across one vector.

In non-trivial deployments, your applications only give tattler some token such as a user ID (e.g. ``481309``), and
tattler looks up what addresses are available for that recipient.

The usual case: tattler looks up the user profile in a database, and determines what addresses are available for it.

Email address? Mobile number?

When a mobile number is not available for a user, tattler will obviously skip sending notifications over SMS for an event,
even if the event avails of templates for SMS notification.


Explicit request
^^^^^^^^^^^^^^^^

Your client application may request to restrict delivery to some vectors only:

.. code-block:: bash

    # use e.g. vector=email,sms
    curl -X POST 'https://127.0.0.1:11503/notification/mywebapp/password_changed/?user=your@email.com&vector=email,sms'

If a vector ist listed which cannot be sent to (content or recipient address not available), the respective vector is ignored.

.. _keyconcepts_notification_events:


Notification events
-------------------

Your applications use tattler to deliver notifications upon certain events,
for example "password changed", "order accepted", "payment failed" etc.

tattler knows itself what actual content to send for the requested event,
because you provide `event templates`_ to it.

You provide event templates as part of tattler configuration.

They are usually written by :doc:`template designers <templatedesigners>`.


Event templates
^^^^^^^^^^^^^^^

Event templates are text which gets expanded to generate an actual notification to send about an event.

tattler uses Jinja as default template processor, so an event template for SMS could look like this::

    Hi {{ user_firstname }}. Be advised that your account password got changed today at {{ appointment_time }}. The address is {{ update_time }}.

Some properties of event templates:

* Are vector-specific, i.e. you'll have different content to deliver the same event via email vs SMS.
* Can be parametrized with variables -- which is why they are "templates". See `Context`_
* Can contain multiple parts. For example, emails include a subject, a body, and potentially HTML content.
* Are "expanded" at delivery time, so you can change them without restarting ``tattler_server``.
* Are stored as files in a directory structure.

Context
^^^^^^^

A context is a set of variables used to expand a template.

Variables available to a template come from various sources:

- tattler provides some :ref:`core variables <templatedesigners:template variables>` itself.
- :ref:`context plug-ins <plugins:context plug-ins>` may add custom variables.
- the client requesting notification may add further variables.


Notification scopes
-------------------

Real-world IT systems are usually composed of multiple components, and each may need to notify users.

For example:

* A web application sends confirmations about created subscriptions.
* A fulfillment system sends shipment confirmations.
* A payment integration backend sends error notifications when a credit card charge failed.

Each such system has its own sets of events to notify, and this set should not be mixed with other applications.

This is what tattler calls a "scope".

A scope is a collection of events under one name, which is usually the name of the system requesting them.

Scopes affect you as a user in 2 ways:

* You need to split your templates by scope.
* You need to indicate the scope for each event you request notification for.

Scopes are **mandatory**: even if you only use tattler from one application, you need to arrange your
notification templates under one scope, and you need to indicate that scope when you issue notification
requests to tattler.


Organizing event templates by scope
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Scopes are non-empty text strings which may only contain letters, numbers and the `_` symbol.
For example ``billing_system2_partners``.

Notification scopes are visible in tattler's :ref:`configuration:TATTLER_TEMPLATE_BASE`: they are
the first-level children (mywebapp, fulfiller, pmtintegrator).

.. code-block:: text
    
    templates_base/
    ├── mywebapp/               <-- a scope
    │   ├── password_changed/    <- an event
    │   └── order_accepted/
    ├── fulfiller/              <-- a scope
    │   ├── order_shipped/       <- an event
    │   ├── delay_occurred/
    │   └── shipping_error/
    └── pmtintegrator/          <-- a scope
        └── cc_charge_failed/    <- an event


Indicating the scope in requests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pass the scope in the URL of your notification requests:

.. code-block:: bash

    #             |-------- server endpoint ---------| |-scope-| |----event----|
    curl -X POST 'https://127.0.0.1:11503/notification/mywebapp/password_changed/?user=your@email.com'

Notification mode
-----------------

Notification mode simplifies development and operations.

It allows client applications to send "real" notification requests -- e.g. with actual client addresses --
while only sending to an `internal address <supervisor recipient>`_ used to verify the output.

Regardless of the mode, notification content is always composed exactly as it would in a "live" environment
(e.g. the "To:" address of emails will include the actual recipient), but the actual notification is
only delivered to an `debug recipient`_ (``debug``) or copied to a
`supervisor recipient`_ (``staging``).

Available modes
^^^^^^^^^^^^^^^

The *mode* is applicable to every notification request, and can be controlled:

- per-request with the ``mode=`` parameter
- at the global level with the :ref:`TATTLER_MASTER_MODE <configuration:TATTLER_MASTER_MODE>` option.

There are 3 modes:

``production``
    Send notification to actual recipient.

``staging``
    Send notification to actual recipient, and also send a copy to debug recipient.
    This is helpful for support teams to keep track of all notifications delivered.

``debug``
    Do not send anything to the actual recipient. Instead, send exclusively to the debug recipient.
    This is useful for developers to safely test their logic operating on real data without
    bothering users nor adapting their code in all systems to avoid doing so.

The default mode is ``debug``, because "better safe than sorry".

Master vs per-request mode
^^^^^^^^^^^^^^^^^^^^^^^^^^

The *master mode* "limits" any per-request mode as a highest possible mode.

That means, a client can request a lower or equal mode than the master, but not a higher one.

.. _supervisor_recipient:

Supervisor recipient
^^^^^^^^^^^^^^^^^^^^

Configured with the :ref:`configuration:TATTLER_SUPERVISOR_RECIPIENT_*` envvar.

All notifications are copied to this address, when they are sent in ``staging`` `notification mode`_.

* The recipient indicated in the request receives the notification.
* The "supervisor recipient" receives a copy of every notification, regardless of the requested recipient.
* The notification content reflects the requested recipient (e.g. the "To:" field of emails, or any reference in the body).
* Log files mention both the requested and the delivered recipients.


Debug recipient
^^^^^^^^^^^^^^^

Configured with the :ref:`configuration:TATTLER_DEBUG_RECIPIENT_*` envvar.

All notifications are sent exclusively to this address, when they are sent in ``debug`` `notification mode`_.

* The recipient indicated in the request receives nothing.
* The "debug recipient" receives every notification requested, regardless of the requested recipient.
* The notification content reflects the requested recipient (e.g. the "To:" field of emails, or any reference in the body).
* Log files mention both the requested and the delivered recipients.
