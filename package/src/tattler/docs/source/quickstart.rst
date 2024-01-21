.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

Quickstart
==========

This guides you to:

1. :ref:`install <quickstart:install>` ``tattler`` into a virtual environment
2. :ref:`run <quickstart:run tattler server>` ``tattler_server``
3. trigger a notification through it, using any of your 3 available options:
    - via :ref:`HTTP <quickstart:Send a notification via HTTP>`
    - or via :ref:`command line <quickstart:Send a notification via command-line>`
    - or via :ref:`python <quickstart:Send a notification via python>`.
4. Write your first :ref:`notification template <quickstart:Provide notification events>`.
5. Do some :ref:`basic customizations <quickstart:Some basic customizations>`.

Install
-------

.. code-block:: bash

   # create and load a virtualenv to install into
   python3 -m venv venv
   . venv/bin/activate

   # install tattler
   pip install tattler

Run tattler server
------------------

.. code-block:: bash

   # run tattler server
   TATTLER_MASTER_MODE=production tattler_server

This causes the following basic scenario:

- ``tattler_server`` listens for requests on `<http://127.0.0.1:11503>`_.
- ``tattler_server`` looks for notifications to send into the local working directory ``.`` plus one "demo" notification embedded into tattler's distribution.
- ``tattler_server`` delivers notification to the actual recipient (no dry-run!) due to the :ref:`TATTLER_MASTER_MODE <configuration:TATTLER_MASTER_MODE>` environment variable.

Send a notification via HTTP
----------------------------

You can do this via plain HTTP request, e.g. using ``curl``:

.. code-block:: bash

   # Open a new terminal and let tattler server run in the previous one
   curl -X POST 'http://127.0.0.1:11503/notification/demoscope/demoevent/?user=your@email.com'

Here's what this does:

- It contacts tattler_server at its REST endpoint ``http://127.0.0.1:11503/notification/``.
- It asks to send the notification for ``demoevent``, which is built into tattler's distribution.
- It asks to send it to ``your@email.com``.

Tried and failed?
^^^^^^^^^^^^^^^^^

There are good chances that you got an error here::

   # on the client
   [{"id": "email:f2591ba6-f25a-4276-b780-26210c0c728b", "vector": "email", "resultCode": 1, "result": "error", "detail": "[Errno 61] Connection refused"}]

   # on the server
   ConnectionRefusedError: [Errno 61] Connection refused

If you did, it's because you have no SMTP server running on ``127.0.0.1``. This is common unless you are testing on a server.

No worries: pointing tattler to your actual SMTP server is as easy as setting environment variable ``TATTLER_SMTP_ADDRESS``.

Read about these `basic customizations <quickstart:Some basic customizations>` for more.

Why demo? Why email?
^^^^^^^^^^^^^^^^^^^^

Now here's a couple of things which might turn your nose:

"Why ``demoevent``? I thought tattler allowed me to send my own notifications!"
   That's right. ``demoevent`` is a template built into tattler to allow demos. We'll look into writing your own notifications :ref:`soon <quickstart:Provide notification events>`.

"Why ``your@email.com``? I thought tattler would look up user information for me!"
   That's right. Tattler really shines when it loads your data for you. We'll look into that in the :ref:`plug-ins section <plugins/index:Tattler plug-ins>`.


Send a notification via command-line
------------------------------------

An alternative is for you to trigger the notification with a command line tool.

Tattler includes a little utility to easily trigger notifications from the command line:

.. code-block:: bash

   tattler_notify -s '127.0.0.1:11503' your@email.com demoscope demoevent

Done!

This does exactly the same as `Send a notification via HTTP`_, using the same REST API, and
actually relying on tattler's python client SDK which we'll look into next.


Send a notification via python
------------------------------

A third option is for you to trigger the notification from python code.

Tattler includes a little python client library:

.. code-block:: python3

   from tattler.client.tattler_py import send_notification

   send_notification('demoscope', 'demoevent', 'your@email.com', srv_addr='127.0.0.1', srv_port=11503)

Again, this code does the same as shown in `Send a notification via HTTP`_: it contacts
``tattler_server`` on the same REST API endpoint.


Provide notification events
---------------------------

What actual content should tattler send, for the event we requested? :ref:`Event templates <keyconcepts/events:Notification events>` tell tattler that.

.. code-block:: bash

   # create a directory to host notification templates and change into it
   mkdir -p ~/notification_events/mywebapp
   cd ~/notification_events/mywebapp
   
   # create a template for an event titled "password changed"
   mkdir password_changed

   # we want event 'password_changed' to send an email notification
   mkdir password_changed/email
   cd password_changed/email
   # so we need a subject and body
   echo 'You successfully changed your password!' > subject
   echo 'Hey!\n\nAccount password changed!' > body_plain

Done. Our notification templates directory now looks like this:

.. code-block:: text

   notification_events/
   └── mywebapp/                 # scope  = mywebapp
       └── password_changed/     # event  = password_changed
           └── email/            # vector = email
               ├── body_plain
               └── subject

Tell tattler server where to find events
------------------------------------------

``tattler_server`` takes the path holding notification event templates from the :ref:`TATTLER_TEMPLATE_BASE <configuration:TATTLER_TEMPLATE_BASE>` environment variable.
So let's restart it with it:

.. code-block:: bash

   # in the terminal which was running script 'tattler_server':
   
   # Stop the running instance with Ctrl-c

   # Re-start the instance with the new path
   TATTLER_TEMPLATE_BASE=~/notification_events TATTLER_MASTER_MODE=production tattler_server


Some basic customizations
-------------------------

Did the command above return a message that includes the below string?

.. code-block::

   ... "result": "error", "detail": "[Errno 61] Connection refused"

That means the machine you're currently running tattler_server on lacks a local SMTP server.

No problem! Here's how you fix it:

.. code-block:: bash

   # in the terminal which was running script 'tattler_server':
   
   # Stop the running instance with Ctrl-c

   # Re-start the instance with the new path
   TATTLER_SMTP_ADDRESS="127.0.0.1:25" TATTLER_SMTP_AUTH="username:password" TATTLER_SMTP_TLS=x TATTLER_TEMPLATE_BASE=~/notification_events TATTLER_MASTER_MODE=production tattler_server

Here we have restarted ``tattler_server`` with the following additional configuration:

* :ref:`TATTLER_SMTP_ADDRESS <configuration:TATTLER_SMTP_ADDRESS>` controls IP address and port number of the SMTP server to use for email delivery
* :ref:`TATTLER_SMTP_AUTH <configuration:TATTLER_SMTP_AUTH>` provides username and password to authenticate at that server with, if set. Remove it if no authentication is required.
* :ref:`TATTLER_SMTP_TLS <configuration:TATTLER_SMTP_TLS>` controls whether to use STARTTLS when talking with that server. Set it to enable it. Remove it to disable it.

Now, how can you possibly pass sensitive information like SMTP credentials
over environment variables on the command line?

You don't 🙂 The :ref:`deployment guide <sysadmins/base_config:Base configuration>`
shows you how to deploy configuration cleanly, privately and maintainably.

Now that you some instant gratification, proceed with learning how to take advantage
of tattler in real-world enterprise scenarios.
