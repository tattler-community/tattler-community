.. image:: https://gitlab.com/tattler/tattler-community/badges/main/pipeline.svg

.. image:: https://gitlab.com/tattler/tattler-community/badges/main/coverage.svg


.. image:: https://gitlab.com/tattler/tattler-community/-/raw/main/package/src/tattler/docs/source/tattler-logo-large-colorneutral.png

Quick start
===========

Install tattler:

.. code-block:: bash

   # create a virtual environment and load it
   python3 -m venv venv
   . venv/bin/activate

   # install tattler into it
   pip install tattler

Run tattler server:

.. code-block:: bash

   TATTLER_MASTER_MODE=production TATTLER_SMTP_ADDRESS="127.0.0.1:25" tattler_server

Trigger a demo notification via HTTP:

.. code-block:: bash

   # make sure to replace ``your@email.com`` with your actual email address
   curl -X POST 'http://127.0.0.1:11503/notification/demoscope/demoevent/?mode=production&user=your@email.com'

... or via command-line utility:

.. code-block:: bash

   # load the same virtual environment where you installed tattler server
   . venv/bin/activate

   # make sure to replace ``your@email.com`` with your actual email address
   tattler_notify -s '127.0.0.1:11503' -m production your@email.com demoscope demoevent

... or via tattler's python SDK:

.. code-block:: python3

   from tattler.client.tattler_py import send_notification

   # make sure to replace ``your@email.com`` with your actual email address
   send_notification('demoscope', 'demoevent', 'your@email.com', mode='production', srv_addr='127.0.0.1', srv_port=11503)

Done! Check out the `quickstart <https://docs.tattler.dev/quickstart.html>`_
in tattler's documentation for a smoother intro.


What is tattler?
================

Do you want to send beautifully branded notifications to your users?

Tattler makes it easy for you. Your application makes a simple HTTP call to tattler:

.. code-block:: bash

   curl -X POST 'http://127.0.0.1:11503/notification/mywebapp/password_changed/?user=123'

and tattler does this for you:

1. Find out what vectors event ``password_changed`` should be notified to. Email? SMS? More?
2. Determine for which of those vectors user ``123`` provided contact data for.
3. Load the respective notification templates.
4. Fetch any data your templates require (with easy-to-write plug-ins). For example: on what plan is the user? Any unpaid invoice?
5. Encode all the resulting content into an actual notification -- e.g. a multi-part MIME email including HTML and plain text parts.
6. Deliver the final content through SMTP and an SMS delivery network.

That's a few chores removed -- so you can focus on your communication, brand and customer journey.


License
=======

Tattler is open-source software (BSD 3-clause license), and includes the features listed above.


Enterprise users
================

Tattler is `enterprise-friendly <https://tattler.dev/#enterprise>`_. Enterprise users avail of a
subscription which provides a bugfixing warranty, extra features, and patronage for the continuity
of the project.
