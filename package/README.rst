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
   tattler_notify -s '127.0.0.1:11503' your@email.com demoscope demoevent

... or via tattler's python SDK:

.. code-block:: python3

   from tattler.client.tattler_py import send_notification

   # make sure to replace ``your@email.com`` with your actual email address
   send_notification('demoscope', 'demoevent', 'your@email.com', srv_addr='127.0.0.1', srv_port=11503)

Done! Check out the `quickstart <https://tattler.readthedocs.io/en/latest/quickstart.html>`_
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

Why tattler?
------------

Introducing Tattler simplifies code and consolidates your communication to your users, making it easier to manage and improve.

**Product managers**
   Will love having a clear view of the communication across the customer journey, and the ease of improving it.

**Template designers**
   Will love the design power and ability to focus on content without technical distractions. 

**Developers**
   Will love the massive simplification in their code — firing notifications without having to collect all ancillary data.

**Customer support**
   Will love being able to easily trace notifications to log trails in other systems that led to firing them. 

**Sys admins**
   Will love having one single point of exit for notifications and the ease of compartmentalizing access to sensitive data. 

Tattler is `well-documented <https://tattler.readthedocs.io>`_, has `safeguarded longevity <https://tattler.dev#enterprise>`_
and has outstanding quality thanks to its exceptional 90%+ test coverage.


License
=======

Tattler is open-source software (BSD 3-clause license), and includes the features listed above.

Enterprise users
================

Tattler is enterprise-friendly. Enterprise customers can purchase subscriptions and get:

- Support from the development team for a fast and secure deployment.
- A bug-fixing guarantee: we'll fix any bug you report in an expedite fashion.
- Level-3 troubleshooting support from our development team.

Enterprise customers get extended, enterprise-specific features:

- Rate control: prevent faulty applications from flooding users with notifications.
- Audit trail: record each delivery along with a positive confirmation ID from its delivery system.
- Auto-text: design HTML emails only, Tattler automatically creates text-form fallback.
- Multilingual support: automatically send which language a user should be notified with.
- Additional delivery vectors to `Telegram <https://telegram.org>`_ and `WhatsApp <https://www.whatsapp.com>`_.

We are grateful to enterprise customers for securing the project's sustainability and
quality the benefit of all.

Commercial users may support tattler in 2 ways:

1. By getting onto an enterprise license -- with the perks listed above.

2. By becoming a sponsor -- with the additional perk of having your company featured as a sponsor on our website and documentation.

Find further information on commercial use on `tattler's website <https://tattler.dev>`_, and write
to ``enterprise at tattler.dev`` for further information such as invoicing, terms, support etc.
