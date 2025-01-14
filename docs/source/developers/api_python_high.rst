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
