Product managers
================

Your role:

- Make a list of events that need to be notified.
- Define which vector each event should be notified to (Email? SMS? more?).
- Draft what approximate information should be included in that notification.

The good news: we have little documentation for you, because you have the
easy part of the work, and because we know you probably wouldn't read more anyway 😜

The process
-----------

We recommend you to proceed as follows:

1. Take (or make) a diagram of your customer journey.
2. Walk across each step, and ask yourself if you'd need to be told anything at/before/after that step.
3. List up the events in the table below.

Hints
^^^^^

- Notification fatigue is a thing.
    - Carefully balance the value of keeping your users connected with the cost of them hearing from you.
    - Make sure there's a reasonable "action" for each event. A weak action suggests a low-value notification.
- Carefully balance how much to tell in the notifications itself vs recall the user to your website to get the information there.

.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

The table
---------

Use something like this, and give it to the template designer when done.

+-----------------------+-------------------------------------------------------+-------+-----+----------------------------------+
| Event                 | Sent when                                             | Email | SMS | Expected action                  |
+=======================+=======================================================+=======+=====+==================================+
| Reservation confirmed | User made final confirmation for a session            | yes   | no  | Refer to it when calling support |
+-----------------------+-------------------------------------------------------+-------+-----+----------------------------------+
| Password changed      | User changed password over website or through support | yes   | yes | Verify if legitimate             |
+-----------------------+-------------------------------------------------------+-------+-----+----------------------------------+
| Appointment reminder  | 2h before appointment due                             | no    | yes | Be time or call to shift         |
+-----------------------+-------------------------------------------------------+-------+-----+----------------------------------+
| CredCard charge error | Subscription charge attempted and failed              | yes   | no  | Log-in and update payment data   |
+-----------------------+-------------------------------------------------------+-------+-----+----------------------------------+

Review
------

Your :ref:`template designer <roles:template designers>` will get back to you with more detailed questions
like what information to include in each event.

You'll also likely review the style of their email stationary, the general tone and more.

Contact points
--------------

Delivering notifications obviously requires the respective address of your recipient,
so you need to plan on where, when and how to collect that.

Here's a summary:

+----------+---------------+---------------------------------------------------------------------------------------------+
| Vector   | Address       | How to collect                                                                              |
+==========+===============+=============================================================================================+
| Email    | Email address | Direct user entry, e.g. during account creation.                                            |
+----------+---------------+---------------------------------------------------------------------------------------------+
| SMS      | Mobile number | Direct user entry, e.g. on 'profile' page.                                                  |
+----------+---------------+---------------------------------------------------------------------------------------------+
| WhatsApp | Mobile number | Direct user entry, e.g. on 'profile' page.                                                  |
+----------+---------------+---------------------------------------------------------------------------------------------+
| Telegram | Telegram ID   | User confirmation, e.g. `Telegram Login button <https://core.telegram.org/widgets/login>`_. |
+----------+---------------+---------------------------------------------------------------------------------------------+

.. caution:: Beware of privacy and compliance!

    Do not send notifications to people without getting prior consent from them.

    This is forbidden in regions with mature privacy regulations like the European Union, and
    frowned upon everywhere else.

    Design your customer journeys to include the collection of your recipient addresses
    with explicit consent.