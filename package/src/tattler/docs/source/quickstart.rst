.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

Quickstart
==========

This guides you to install ``tattler`` using `Jinja <https://https://jinja.palletsprojects.com/>`_ as template processor.

Install tattler with Jinja as template processor
--------------------------------------------------

.. code-block:: bash

   # create and load a virtualenv to install into
   python3 -m venv venv
   . venv/bin/activate

   # install tattler with the Jinja package (use quotes to avoid shell interference)
   pip install 'tattler[Jinja]'

Run tattler server
--------------------

.. code-block:: bash

   # run tattler server
   MASTER_MODE=production tattler_server

This causes the following basic scenario:

- ``tattler_server`` listens for requests on `<http://127.0.0.1:11503>`_.
- ``tattler_server`` looks for notifications to send into the local working directory ``.``
- ``tattler_server`` delivers notification to the actual recipient (no dry-run!) due to the :ref:`MASTER_MODE <configuration:TATTLER_MASTER_MODE>` environment variable.

Attempt to send a notification
------------------------------

.. code-block:: bash

   # Open a new terminal and let tattler server run in the previous one
   curl -X POST 'http://127.0.0.1:11503/notification/mywebapp/password_changed/?user=your@email.com'

... which fails miserably because we have not given tattler any notification to send. So let's do that.

Provide notification events
---------------------------

What actual content should tattler send, for the event we requested? :ref:`Event templates <keyconcepts:Notification events>` tell tattler that.

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

``tattler_server`` takes the path holding notification event templates from the :ref:`TEMPLATE_BASE <configuration:TATTLER_TEMPLATE_BASE>` environment variable.
So let's restart it with it:

.. code-block:: bash

   # in the terminal which was running script 'tattler_server':
   
   # Stop the running instance with Ctrl-c

   # Re-start the instance with the new path
   TEMPLATE_BASE=~/notification_events MASTER_MODE=production tattler_server


Send notification
-----------------

.. code-block:: bash

   # Open a new terminal while letting tattler server run previous console
   curl -X POST 'http://127.0.0.1:11503/notification/mywebapp/password_changed/?user=your@email.com'

This finally succeeds. The console of ``tattler_server``'s process will show you the details of its delivery attempt.

Still failing?
^^^^^^^^^^^^^^

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

Done!

Now that you some instant gratification, proceed with learning how to take advantage
of tattler in real-world enterprise scenarios.
