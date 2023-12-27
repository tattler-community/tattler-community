.. tattler documentation master file, created by
   sphinx-quickstart on Tue Dec  5 13:35:55 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tattler -- an enterprise notification system
============================================

Tattler is an enterprise notification system. It allows you to send notifications from any
application like this:

.. code-block:: bash

   curl -X POST 'http://127.0.0.1:11503/notification/mywebapp/password_changed/?user=123'

Tattler then sends a beautiful, branded notification to the user
across email and/or SMS.

Tattler does the heavy lifting of notifications for you:

- Personalize notifications to each user with templates.
- Compose compatible HTML emails with text fallback.
- Look up user contacts to deliver email or SMS.
- Tag notifications with unique IDs to aid Support teams.

... so you can focus on your customer journey and brand.

Introducing Tattler usually simplifies a lot of code, and consolidates communication
to your users making it easier to manage and improve.

Your product managers will love having a trivial process to organize communication across the
customer journey, and the resulting visibility.

Your template designers will love the flexibility and ability to care of user-visible content
without distractions.

Your devs will love the massive simplification in their code for just triggering
notifications with one HTTP POST request and without having to seek all ancillary data.

Your support team will love having access to all notifications sent to users,
and its trivial root-cause analysis across many systems.

Your sys admins will love having one single point of exit for user notifications, and the
ability to trigger notifications across different containers or even servers.

System Context
^^^^^^^^^^^^^^

.. mermaid::
   
   C4Context
       title System Context diagram for Tattler
       Enterprise_Boundary(b0, "Enterprise context") {
           Person(ProdMan, "Product manager", "Owns the customer journey.")
           Person(TemplDev, "Template developer", "Implements graphical<br/>and voice brand.")
           Person(SWDev, "Software Developer", "Codes systems which,<br/>trigger notifications")
           Person(SysAdm, "System Administrator", "Deploy and operate systems.")
           System(Tattler, "Tattler", "Sends notifications<br/>over various vectors.")

           System_Ext(WebApp, "WebApp")
           System_Ext(BillSys, "Billing System")
           System_Ext(BookingSys, "Booking System")

           Rel(ProdMan, Tattler, "Define notifications<br/>across customer journey.")
           Rel(TemplDev, Tattler, "Author and style<br/>notifications.")
           Rel(SWDev, Tattler, "Build notification triggers<br/>into existing systems.")
           Rel(SysAdm, Tattler, "Deploy, configure,<br/>secure.")

           Rel(WebApp, Tattler, "Trigger notification")
           Rel(BillSys, Tattler, "Trigger notification")
           Rel(BookingSys, Tattler, "Trigger notification")
       }
       Person(User, "User", "Consumes services of enterprise.")
       System(SMTP, "SMTP", "E-mail delivery<br/>system")
       System(SMS, "SMS", "SMS delivery<br/>system")
       Rel(Tattler, SMTP, "Deliver email<br/>notification")
       Rel(Tattler, SMS, "Deliver SMS<br/>notification")
       Rel(User, Tattler, "Receive<br/>notifications.")


Advanced features
-----------------

Additionally, Tattler supports some advanced deployment scenarios:

- Deliver notifications from components on different servers or inside containers.
- Tokenize contact information, so components only deal with user IDs, and Tattler expands the associated user information.
- Collect additional variables about a user in one place (account type, resources used, solvency, ...), make them available to notifications from all subsystems.
- Restrict access to your users' contact data in your database to Tattler only, preventing data leaks in case of a hack.

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
- Multi-lingual support: automatically send which language a user should be notified with.
- Additional delivery vectors to `Telegram <https://telegram.org>`_ and `WhatsApp <https://www.whatsapp.com>`_.

We are grateful to enterprise customers for securing the project's sustainability and
quality the benefit of all.

Commercial users may support tattler in 2 ways:

1. By getting onto an enterprise license -- with the perks listed above.

2. By becoming a sponsor -- with the additional perk of having your company featured as a sponsor on our website and documentation.

Find further information on commercial use on `tattler's website <https://tattler.dev>`_, and write
to ``enterprise at tattler.dev`` for further information such as invoicing, terms, support etc.


Contents
========

Proceed to the following contents to learn about deploying and using Tattler for your project.

.. toctree::
   :maxdepth: 2
   
   quickstart
   roles
   keyconcepts
   productmanagers
   templatedesigners
   developers
   plugins
   sysadmins
   configuration


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
