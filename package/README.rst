Tattler -- enterprise notification system
===========================================

Overview
--------

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


Advanced features
-----------------

Additionally, Tattler supports some advanced deployment scenarios:

- Deploy containerized components, that only communicate via TCP.
- Deliver notifications from multiple components, even if on different servers (billing, web application, batch processes etc)
- Tokenize contact information, so components only deal with user IDs, and Tattler expands the associated user information.
- Collect additional variables about a user in one place (free/paid, resources used, ...), and make it available to notifications from all subsystems.
- Insulate notification system from other systems.
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
