WhatsApp templates
==================

.. note:: This feature is only available in Tattler's `enterprise edition <https://tattler.dev#enterprise>`_.

+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Address type           | Mobile number, in `E.164 <https://www.bulksms.com/developer/json/v1/>`_ format.                                              |
+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Default gateway        | `WhatsApp's business platform <https://developers.facebook.com/docs/whatsapp/cloud-api/>`_                                   |
+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Encoding               | UTF-8.                                                                                                                       |
+------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Content type           | Plain text or markdown.                                                                                                      |
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
content into a text file named ``body.txt`` within it::

    templates_base/
    └── mywebapp/
        └── password_changed/
            └── whatsapp/                 <- WhatsApp vector
                └── body.txt              <- content template

If your interaction model requires you to contact the user first, you may find that WhatsApp requires
you to open new conversations with a template message, instead of free text. Template messages must be
created in your WhatsApp's business account, and approved by a WhatsApp moderator.

Tattler allows you to send WhatsApp templates. Simply have your event template be::

    :template:whatsapp_template_name

Tattler will then ask WhatsApp to deliver template ``whatsapp_template_name``. Passing template parameters
to WhatsApp is not currently supported, so make sure your template does not include any.


.. caution:: The WhatsApp platform poses some requirements to deliver messages!
	
    Meta -- the company owning WhatsApp, poses a number of requirements to send WhatsApp messages:

    - You need to setup a `developer account <https://developers.facebook.com>`_ and `business account <https://business.facebook.com>`_.

    - You need to register a mobile number that your messages will appear as sent from. Meta will provide you one such number for testing purposes.

    - There are fees to pay beyond a certain volume of messages.

    - Your recipient obviously needs to have WhatsApp active on their mobile phone. WhatsApp provides no feedback on whether this is the case, so Tattler will always return success when delivering to WhatsApp.

    - New requirements are introduced over time. For example, you may be only be able to open a conversation with a template message, unless the user had contacted your source number first.
    
    See `WhatsApp Cloud API's documentation <https://developers.facebook.com/docs/whatsapp/cloud-api/>`_
    for more details.
