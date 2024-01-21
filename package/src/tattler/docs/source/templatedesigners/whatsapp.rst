WhatsApp templates
------------------

.. note:: This feature is only available in Tattler's `enterprise edition <https://tattler.dev#enterprise>`_.

+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Address type           | Mobile number, in `E.164 <https://www.bulksms.com/developer/json/v1/>`_ format.                                              |
+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Default gateway        | `WhatsApp's business platform <https://developers.facebook.com/docs/whatsapp/cloud-api/>`_                                   |
+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Encoding               | UTF-8.                                                                                                                       |
+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Content type           | Plaintext or markdown.                                                                                                       |
+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Maximum content length | 1024 characters.                                                                                                             |
+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Emojis                 | Yes.                                                                                                                         |
+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Upstream cost          | Limited free tier, then payment by volume. See `WhatsApp pricing <https://developers.facebook.com/docs/whatsapp/pricing/>`_. |
+------------------------+------------------------------------------------------------------------------------------------------------------------------+


WhatsApp templates are similar to SMS templates.

.. hint:: WhatsApp requires you to have the user's mobile phone number as the address of the recipient.

If you want to notify an event via WhatsApp, add the ``whatsapp`` folder within the event folder, and its
content into a text file named ``body`` within it::

    templates_base/
    └── mywebapp/
        └── password_changed/
            └── whatsapp/                 <- WhatsApp vector
                └── body                  <- content template


.. caution:: The WhatsApp platform poses some requirements to deliver messages!
	
    Meta -- the company owning WhatsApp, poses a number of requirements to send WhatsApp messages:

    - You need to setup a business account.

    - You need to indicate a mobile number that your messages will appear as sent from.

    - There are fees to pay beyond a certain volume of messages.

    - Your recipient obviously needs to have WhatsApp active on their mobile phone. WhatsApp provides no feedback on whether this is the case, so Tattler will always return success when delivering to WhatsApp.

    See `WhatsApp Cloud API's documentation <https://developers.facebook.com/docs/whatsapp/cloud-api/>`_
    for more details.

