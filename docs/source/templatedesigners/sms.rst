SMS templates
=============

+------------------------+---------------------------------------------------------------------------------+
| Address type           | Mobile number, in `E.164 <https://www.bulksms.com/developer/json/v1/>`_ format. |
+------------------------+---------------------------------------------------------------------------------+
| Default gateway        | `BulkSMS.com <https://bulksms.com>`_                                            |
+------------------------+---------------------------------------------------------------------------------+
| Encoding               | `GSM 03.38 <https://en.wikipedia.org/wiki/GSM_03.38>`_                          |
+------------------------+---------------------------------------------------------------------------------+
| Content type           | Plain text with some accented characters.                                       |
+------------------------+---------------------------------------------------------------------------------+
| Maximum content length | Multiples of 160 characters if ASCII; 70 if any unicode character.              |
+------------------------+---------------------------------------------------------------------------------+
| Emojis                 | Yes, but they shorten the message length to 70 characters.                      |
+------------------------+---------------------------------------------------------------------------------+
| Costs                  | See `BulkSMS pricing <https://www.bulksms.com/pricing/>`_. No affiliation.      |
+------------------------+---------------------------------------------------------------------------------+

.. hint:: SMS delivery through Tattler requires an account at `BulkSMS.com`_ .

    Tattler relies on the `bulksms library <https://pypi.org/project/bulksms/>`_ for final delivery of
    SMS to their mobile network, so you need an account with `BulkSMS.com <https://www.bulksms.com>`_ and
    some delivery credits in order to deliver your SMS messages.
    
    Tattler has no affiliation with BulkSMS. Alternative gateways can be easily implemented, but none
    has been, yet.

SMS notifications are less common than email notifications, but let's start here because
their simplicity builds a base to understand the more complex emails.

Event templates are some text which gets expanded at delivery time into the final text.

SMS templates are organized as follows inside the event's folder::

    templates_base/
    └── mywebapp/
        └── password_changed/
            └── sms/                <- sms vector
                └── body.txt        <- content template

This SMS template file may contain some content like this::

    Hi {{ user_firstname }}. Be advised that your account password got changed today at {{ appointment_time }}. The address is {{ update_time }}.

You already picture what the user will actually be texted.

The message encoding is ASCII plus a `small set of frequent-use accented characters <https://en.wikipedia.org/wiki/GSM_03.38>`_.

Such messages may be up to 160 characters long; ASCII messages longer than this will be delivered
as multiple messages, which the receiving mobile phone is capable of concatenating back together.
The delivery price will obviously multiply correspondingly.

Messages that include characters beyond the GSM_03.38 set -- such as an emoji, or Arabic --
can be sent too. This will reduce the maximum message length to 70. Longer content is supported
(up to 400 characters) and will be broken down into multiple messages, and be priced correspondingly.

BulkSMS supports multi-part messages, i.e. content exceeding a single-message length will be broken down into multiple messages,
which the receiving mobile phone will be able to concatenate back together. 
