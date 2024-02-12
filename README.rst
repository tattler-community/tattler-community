.. image:: https://gitlab.com/tattler/tattler-community/badges/main/pipeline.svg

.. image:: https://gitlab.com/tattler/tattler-community/badges/main/coverage.svg


.. image:: https://gitlab.com/tattler/tattler-community/-/raw/main/docs/source/tattler-logo-large-colorneutral.png

Table of contents
=================

1. `What is tattler?`_
2. `Examples`_
3. `Quick start`_
4. `License`_
5. `Enterprise users`_
6. `Links`_

What is tattler?
================

Are you building an online service and need to send beautiful, branded notifications via email or SMS to your users?

Tattler makes that easy for you. Your application makes a simple HTTP call to tattler:

.. code-block:: bash

   curl -X POST 'http://127.0.0.1:11503/notification/mywebapp/password_changed/?user=123'

and tattler does this for you:

1. Load your templates for event ``password_changed``, and see where it should be notified. (Email? SMS? More?)
2. Load the email address and mobile number for user ``123`` as required -- with trivial-to-write plug-ins.
3. Load any variable that your templates require -- with trivial-to-write plug-ins. (What plan is the user on? How much of the plan is used up?)
4. Expand the template and encode the content into an actual notification -- e.g. a multi-part MIME email with HTML and plain text fallback.
5. Deliver the final content through SMTP and an SMS delivery network.

Tattler is designed with simplicity in mind. It strives to be easy to adopt and useful among common needs -- so you
can focus on your communication, brand and customer journey.

If your system sends notifications from multiple different softwares -- say a web application, a billing daemon,
and a cron job which monitors inventory -- then your simplification gains with tattlers get multipled 🚀

.. image:: https://gitlab.com/tattler/tattler-community/-/raw/main/demos/tattler-benefit.png


Examples
========

Here's an example notification with HTML email, and its corresponding plain text version:

.. list-table:: 

    * - .. figure:: https://gitlab.com/tattler/tattler-community/-/raw/main/demos/tattler-notification-example-email-html.png

           Fig 1. Example notification as HTML email.

      - .. figure:: https://gitlab.com/tattler/tattler-community/-/raw/main/demos/tattler-notification-example-email-plaintext.png

           Fig 2. Its corresponding plain text version.

And here's an example SMS notification:

.. image:: https://gitlab.com/tattler/tattler-community/-/raw/main/demos/tattler-notification-example-sms.png


Quick start
===========

Install tattler:

.. code-block:: bash

   # create and load a virtualenv to install into
   mkdir ~/tattler_quickstart
   python3 -m venv ~/tattler_quickstart/venv
   . ~/tattler_quickstart/venv/bin/activate

   # install tattler into it
   pip install tattler

Run tattler server:

.. code-block:: bash

   export TATTLER_MASTER_MODE=production
   
   # if you need to customize your SMTP settings
   export TATTLER_SMTP_ADDRESS="127.0.0.1:25"
   export TATTLER_SMTP_AUTH="username:password" # you will learn secure configuration later
   export TATTLER_SMTP_TLS=yes

   # run tattler server on default 127.0.0.1:11503
   tattler_server

Trigger a demo notification via HTTP:

.. code-block:: bash

   # in a new terminal:
   
   # replace ``your@email.com`` with your actual email address
   curl -X POST 'http://127.0.0.1:11503/notification/demoscope/demoevent/?mode=production&user=your@email.com'

... or via command-line utility:

.. code-block:: bash

   # load the same virtual environment where you installed tattler server
   . ~/tattler_quickstart/venv/bin/activate

   # replace ``your@email.com`` with your actual email address
   tattler_notify -s '127.0.0.1:11503' -m production your@email.com demoscope demoevent

... or via tattler's python SDK:

.. code-block:: python3

   from tattler.client.tattler_py import send_notification

   # replace ``your@email.com`` with your actual email address
   send_notification('demoscope', 'demoevent', 'your@email.com', mode='production', srv_addr='127.0.0.1', srv_port=11503)

Done!

Want more? Proceed to the `complete quickstart <https://docs.tattler.dev/quickstart.html>`_ in tattler's documentation
for plug-ins, deployment and more.


Help us be better
=================

Here's how you can help:

- ⭐️ star our `repository <https://gitlab.com/tattler/tattler-community/>`_ if you like tattler. That's our go-to place whenever we feel sad! 😁
- `Let us know <mailto:users@tattler.dev>`_ that you are using tattler. How long? For what organization? What is your feedback?
- Let your friends know about tattler. If you found it useful, chances are they will too.
- Report any `issue <https://gitlab.com/tattler/tattler-community/-/issues>`_ in our code or docs. We take those seriously.
- See ways to contribute in our `contributing guidelines <https://gitlab.com/tattler/tattler-community/-/blob/main/CONTRIBUTING.md>`_.


License
=======

Tattler is open-source software (BSD 3-clause license), and includes the features listed above.


Enterprise users
================

Tattler is `enterprise-friendly <https://tattler.dev/#enterprise>`_. Enterprise users avail of a
subscription which provides a bugfixing warranty, extra features, and patronage for the continuity
of the project.


Links
=====

- `Tattler website <https://tattler.dev>`_
- `Documentation <https://docs.tattler.dev>`_
- `HTTP API spec <https://tattler.dev/api-spec/>`_
- `Repository <https://gitlab.com/tattler/tattler-community/>`_
