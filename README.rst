.. |badge_pipeline| image:: https://gitlab.com/tattler/tattler-community/badges/main/pipeline.svg

.. |badge_coverage| image:: https://codecov.io/gh/tattler-community/tattler-community/graph/badge.svg?token=Q5KGRSR0WT 
   :target: https://codecov.io/gh/tattler-community/tattler-community

.. |badge_release| image:: https://img.shields.io/badge/Latest%20Release-1.5.1-blue

.. |badge_pyver| image:: https://img.shields.io/badge/py-3.9%20|%203.10%20|%203.11%20-blue

.. |badge_license| image:: https://img.shields.io/badge/license-BSD_3--clause-blue


|badge_pipeline| |badge_coverage| |badge_release| |badge_pyver| |badge_license|

.. image:: https://raw.githubusercontent.com/tattler-community/tattler-community/main/docs/source/tattler-logo-large-colorneutral.png

🚩 Table of contents
====================

1. `👀 What is tattler?`_
2. `🤩 Examples`_
3. `🚀 Quick start`_
4. `💙 Help us be better`_
5. `🎖️ License`_
6. `📈 Enterprise users`_
7. `📌 Links`_

👀 What is tattler?
===================

Are you building an online service and need to send beautiful, branded notifications via email or SMS to your users?

Tattler makes that easy for you. Your application makes a simple HTTP call to tattler:

.. code-block:: bash

   curl -X POST 'http://127.0.0.1:11503/notification/mywebapp/password_changed/?user=123'

Tattler helps you with these:

1. **Templates**: Load templates for event ``password_changed`` for email, SMS etc.
2. **Addressbook**: Fetch the user's email address and mobile number from your DB (with trivial-to-write plug-ins).
3. **Template data**: Fetch variables for your templates from your DB (with trivial-to-write plug-ins).
4. **MIME**: Package a multi-part email with HTML+text fallback.
5. **Delivery**: Send the content through SMTP and an SMS delivery network.
6. **Dev mode**: Let your applications trigger notifications to the real user and have tattler only deliver it to your debug address.

Tattler is designed with simplicity in mind. It strives to be easy to adopt and useful among common needs -- so you
can focus on your communication, brand and customer journey.

If your system sends notifications from multiple different softwares -- say a web application, a billing daemon,
and a cron job which monitors inventory -- then your simplification gains with tattlers get multipled 🚀

.. image:: https://raw.githubusercontent.com/tattler-community/tattler-community/main/demos/tattler-benefit.png

😵‍💫 Don't beat around the bush!
---------------------------------

Tattler is:

- a server
- written in python
- for UNIX systems
- that exposes a REST interface
- which your applications contact
- to request delivery of notifications to users.


🤩 Examples
==============

Here's a little gallery of notifications sent via tattler to email and SMS:

.. list-table:: 

    * - .. figure:: https://raw.githubusercontent.com/tattler-community/tattler-community/main/demos/tattler-notification-example-email-html.png

           Fig 1. Example notification as HTML email.

      - .. figure:: https://raw.githubusercontent.com/tattler-community/tattler-community/main/demos/tattler-notification-example-email-plaintext.png

           Fig 2. Its corresponding plain text version.

    * - .. figure:: https://raw.githubusercontent.com/tattler-community/tattler-community/main/demos/tattler-notification-demo-email-html-light.png

           Fig 3. Tattler's demo notification with reusable code samples.

      - .. figure:: https://raw.githubusercontent.com/tattler-community/tattler-community/main/demos/tattler-notification-example-sms.png

           Fig 4. A SMS notification.


🚀 Quick start
=================

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


💙 Help us be better
=======================

Here's how you can help, in order of increasing time commitment 🙂

- ⭐️ star our `repository <https://github.com/tattler-community/tattler-community/>`_ if you like tattler. That's our go-to place whenever we feel sad! 😁
- `Let us know <mailto:users@tattler.dev>`_ that you are using tattler. How long? For what organization? What is your feedback?
- Blog about tattler. If you found tattler useful, chances are your post will be useful to others too.
- Report any `issue <https://github.com/tattler-community/tattler-community/issues>`_ in our code or docs. We take those seriously.
- Package tattler for your distribution. Else Ubuntu, Debian, CentOS and FreeBSD will serve the most people.
- Implement a client for tattler in another language.

See our `contributing guidelines <https://raw.githubusercontent.com/tattler-community/tattler-community/main/CONTRIBUTING.md>`_ for details.


🎖️ License
=============

Tattler is open-source software (BSD 3-clause license).


📈 Enterprise users
======================

Tattler is `enterprise-friendly <https://tattler.dev/#enterprise>`_. Enterprise users avail of a
subscription which provides a bugfixing warranty, extra features, and patronage for the continuity
of the project.


📌 Links
===========

- `Tattler website <https://tattler.dev>`_
- `Documentation <https://docs.tattler.dev>`_
- `HTTP API spec <https://tattler.dev/api-spec/>`_
- `Repository <https://github.com/tattler-community/tattler-community/>`_
