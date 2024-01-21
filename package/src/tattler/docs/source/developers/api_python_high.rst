High-level Python API
---------------------

tattler comes with an open-source python SDK.

The high-level API in it allows you to trigger a notification with one line of code:

.. code-block:: python

    # high-level API
    from tattler.client.tattler_py import send_notification

    success, details = send_notification('mywebapp', 'password_changed', 'your@email.com', {'var1': 1, 'var2': 'two'}, correlationId='1234')
    if not success:
        print(details)

Here you notice additional parameters:

* A client context: a dictionary containing variable definitions, which tattler will pass on to the template.
* A correlationId: a string identifying the transaction at the client, which tattler will log into its own logs and audit trails.

Here's a brief reference of the function:

.. automodule:: tattler.client.tattler_py
    :members: send_notification

Additionally, the python client is controlled by the following **environment variables**:

``TATTLER_SERVER``
    Values: ``ip4:port`` or ``[ip6]:port``.

    Default: ``127.0.0.1:11503``.
    
    Address to connect to for tattler server.

``LOG_LEVEL``
    Values: ``debug``, ``info``, ``warning``, ``error``.

    Default: ``info``.

    Only log entries at or higher than this severity.


