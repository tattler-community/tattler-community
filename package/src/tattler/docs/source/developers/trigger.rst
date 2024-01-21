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
tattler resolves all necessary contacts by itself with an :ref:`addressbook plug-in <plugins/addressbook:addressbook plug-ins>`.

You currently have 3 APIs to call tattler:

1. an HTTP API

2. A high-level python API.

3. A low-level python API.
