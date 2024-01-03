Developers
==========

Your role:

- Determine what systems need to trigger notifications for the :ref:`defined events <productmanagers:the table>`.
- Implement logic to call tattler upon each of those events.

Potential follow-up tasks:

- Decide if user contacts should be looked up by every system of yours, or rather tattler. In the latter case, you'll want to write an :ref:`addressbook plug-in <plugins:addressbook plug-ins>`.
- Decide with your :ref:`template designer <roles:template designers>` if several templates need some additional variables that you do not want to load in every system. In which case, you'll want to write a :ref:`context plug-in <plugins:context plug-ins>`.


What systems trigger notifications (scope)
------------------------------------------

Start from the :ref:`events list <productmanagers:the table>` from your
product manager.

Understand what events must be notified, and what systems
in your overall system should trigger those.

Map each notification to its triggering system:

+-----------------------+-------------------+
| Event                 | Triggering system |
+=======================+===================+
| Reservation confirmed | myWebApp          |
+-----------------------+-------------------+
| Password changed      | myWebApp          |
+-----------------------+-------------------+
| Appointment reminder  | myBookingSys      |
+-----------------------+-------------------+
| CredCard charge error | pmtintegrator     |
+-----------------------+-------------------+

Each system that triggers a notification will identify itself as
a :ref:`scope <keyconcepts:notification scopes>` to tattler.

Communicate the scopes to your :ref:`template designer <roles:template designers>`
so they can start organizing the templates for each event.


Code a notification trigger
---------------------------

Pick a system to triger a notification. Write code to have this system make an HTTP
POST request to tattler server's API.

In ``curl`` the request to send notification ``password_changed`` in scope ``mywebapp`` to user
``your@email.com`` looks like this:

.. code-block:: bash

    curl -X POST 'http://127.0.0.1:11503/notification/mywebapp/password_changed/?user=your@email.com'

Notice the 3 essential parameters:

1. The scope name: ``mywebapp``

2. The event name: ``password_changed``

3. The recipient ID: ``your@email.com``

You usually do **not** provide the user's address from the triggering system.
Instead, your backend systems only provide some ID (e.g. user ID) from which
tattler resolves all necessary contacts by itself with an :ref:`addressbook plug-in <plugins:addressbook plug-ins>`.

You currently have 3 APIs to call tattler:

1. an HTTP API

2. A high-level python API.

3. A low-level python API.


HTTP API
--------

You open a TCP socket and send a HTTP POST request to tattler_server.

This API allows you to:

* Trigger notifications.
* List scopes.
* List events within a scope.
* List vectors for an event.

See the interactive `OpenAPI spec <https://tattler.dev/api-spec/>`_ for details.


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


Low-level Python API
--------------------

Use this API if you need fine-grained control of notifications, for example if you want to
send a large number of notifications in one go and want to reuse the HTTP connection.

.. code-block:: python

    from tattler.client.tattler_py import TattlerClientHTTP

    # refer to templates in folder template_base/my_application. Debug mode = only send to test address, not to actual recipient
    n = TattlerClientHTTP(scope_name='myapplication', srv_addr='127.0.0.1', srv_port=11503, mode='debug')
    # send notification for event 'my_event' over email only to user #20 (tattler resolves actual email address)
    n.send(vectors=['email'], event='my_event', recipient='20')

    # send template which requires expanding variables
    n.send(vectors=['email'], event='my_event', recipient='20', context={'var1': 'value1', 'var2': 'value2'})

    # set priority flag, and use correlationID to associate throughout delivery chain
    n.send(vectors=['email'], event='my_event', recipient='20', priority=True, correlationId='12398724')

    # utility to generate correlationIds
    from tattler.client.tattler_py import mk_correlation_id
    print(mk_correlation_id())
    # NkvgXrYI



Correlation Ids
---------------

In complex enterprise systems, a transaction often occurs across three or more subsystems.

1. The resource-management system of a supplier might signal that a consultant is no longer available.

2. The company's booking system then invalidates all open appointments for that consultant, and trigger a notification with tattler.

3. tattler sends the notification.

3 separate systems and log files -- a nightmare for the support team when it has to investigate
why a client was notified of a cancellation.

Enter correlation identifiers:

1. The supplier's resource-management system -- the "origin" -- creates a random, unique string called ``correlationId``. It mentions this string into its own logs, and passes it on to the company's booking system.

2. The company's booking system mentions this string as-is in its own log entries about the transaction. It also passes it on again to tattler when triggering the notification.

3. tattler again mentions this string as-is in its own logs about the transaction.

The support team can now simply grep log files from the 3 systems and gain access to the entire
trace of this transaction across all systems.
