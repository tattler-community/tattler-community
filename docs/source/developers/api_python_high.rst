High-level Python API
---------------------

tattler comes with an open-source python SDK.

The high-level API in it allows you to trigger a notification with one line of code:

.. code-block:: python

    # high-level API
    from tattler.client.tattler_py import send_notification

    success, details = send_notification(   \
        'mywebapp', 'password_changed', 'your@email.com', \
        context={'var1': 1, 'var2': 'two'})

    if not success:
        print(details)

This calls to notify:

- scope ``mywebapp``
- event name ``password_changed``
- to recipient ``your@email.com``
- using the given context, i.e. variables that tattler server will expand the respective :ref:`event template <keyconcepts/events:event templates>` with.

Context
=======

Tattler client allows you to pass complex objects -- like a Django model object -- into a notification context:

.. code-block:: python
    
    # sample model code:
    from django.db import models
    from django.contrib.auth.models import User
    
    class Address(models.Model):
        street_and_number = models.CharField(max_length=256)
        postal_code = models.CharField(max_length=20)
        city = models.CharField(max_length=256)
        country_code = models.CharField(max_length=6)

    class UserProfile(models.Model):
        user = models.ForeignKey(User, related='profile')
        birthday = models.DateField()
        sex = models.CharField(max_length=1, options=['F', 'M'])
        address = models.ForeignKey(Address)

    # sample view code:
    uprof = UserProfile.object.get(pk=1)
    send_notification('mywebapp', 'password_changed', uprof.user.email, \
        context=uprof)


Tattler will automagically serialize them to the deepest extent possible:

- datetime, date, time and timedelta fields are automatically serialized in a way that the server can reconstruct to datetime, date, time and timedelta objects into your templates.

- When passed Django model objects, tattler will recurse into related objects linked with ForeignKeys and embed them into your context.


.. code-block:: python

    # Your template at will receive this context from tattler-server:
    context = {
        'user': {
            'username': 'johndoe1990',
            'date_joined': datetime(2020, 2, 28, 10, 20, 35)
            'email': 'user@email.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'is_staff': False,
            'is_active': True,
            'is_superuser': False,
            # ...
        },
        'birthday': date(1990, 12, 25),
        'sex': 'M',
        'address': {
            'street_and_number': 'Palace of Nations, Av. de la Paix 8-14',
            'postal_code': '1211',
            'city': 'Genève',
            'country_code': 'CHE'
        }
    }


This is very powerful and allows you to pass a lot of data very easily into your notifications.

If your needs exceed this capability, look into :ref:`Tattler plug-ins <plugins/index:Tattler plug-ins>` to load data directly into tattler-server.


Attachments
===========

Email notifications can carry inline images and file attachments. Pass them
via the ``attachments`` keyword to :func:`send_notification`:

.. code-block:: python

    from pathlib import Path
    from tattler.client.tattler_py import send_notification

    success, details = send_notification(
        'mywebapp', 'invoice_ready', 'alice@example.com',
        context={'user_firstname': 'Alice'},
        attachments={
            'logo@brand':  Path('/srv/branding/logo.png'),       # local file
            'terms.pdf':   'https://internal/legal/terms.pdf',   # remote URL
        },
    )

The ``attachments`` value is a dict whose keys follow the wire convention:

* A key containing ``@`` is the **Content-ID** of an inline image, referenced
  from the HTML body as ``<img src="cid:logo@brand">``. Image type is
  auto-detected from the bytes (PNG, JPEG, GIF, WebP, SVG).
* A key without ``@`` is the **filename** of a regular attachment; its
  extension drives the MIME type.

Each value must be one of:

:class:`pathlib.Path`
    A local file. The SDK reads it and base64-encodes the bytes before posting.

``str`` (``http://...`` or ``https://...``)
    A URL the **server** will fetch. Other schemes are rejected client-side.

See the :ref:`HTTP API reference <developers/api_http:Sending attachments>`
for size limits, MIME-detection rules, and the trust model.

.. note::
    To use raw bytes you already have in memory, write them to a temporary
    file and pass the resulting :class:`~pathlib.Path`. For low-level access
    to the wire format, set ``context['_attachments']`` directly -- but you
    cannot pass both ``attachments=`` and ``context['_attachments']`` in the
    same call (it raises :class:`ValueError`).


Server address
==============

By default ``send_notification()`` looks up the address of the tattler server to contact from environment variable ``TATTLER_SRV_ADDRESS``
(see format below), and falls back to defaults ``127.0.0.1:11503`` if that's not set or empty.

The address of the server can also be provided explicitly. Here's a more advanced example:

.. code-block:: python

    # high-level API
    from tattler.client.tattler_py import send_notification

    success, details = send_notification(                   \
        'mywebapp', 'password_changed', 'your@email.com',   \
        srv_addr='192.168.1.1', srv_port=11503,             \
        correlationId='myprog:38ffae84')

This points tattler_client to reach the server at the respective address and port.

This example additionally provides a :ref:`correlationId <developers/correlationid:Correlation Ids>`.
That's a string identifying the transaction at the client,
which tattler will log into its own logs to aid cross-system troubleshooting.

Here's a brief reference of the function:

.. automodule:: tattler.client.tattler_py
    :members: send_notification

Additionally, the python client is controlled by the following **environment variables**:

``LOG_LEVEL``
    Values: ``debug``, ``info``, ``warning``, ``error``.

    Default: ``info``.

    Only log entries at or higher than this severity.

``TATTLER_SERVER_ADDRESS``
    Values: address:port -- address is an IPv4 or IPv6 address.

    Default: ``127.0.0.1:11503``

    Contact the server on this address and TCP port.
