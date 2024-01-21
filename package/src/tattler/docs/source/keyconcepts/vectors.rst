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
            └── sms/
                └── body

See docs for :ref:`template designers <templatedesigners/index:Template designers>`.


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


