Telegram templates
------------------

.. note:: This feature is only available in Tattler's `enterprise edition <https://tattler.dev#enterprise>`_.

+------------------------+----------------------------------------------------------------------------------------------------------+
| Address type           | Telegram ID. Retrieve it e.g. with a `Telegram Login Widget <https://core.telegram.org/widgets/login>`_. |
+------------------------+----------------------------------------------------------------------------------------------------------+
| Default gateway        | `Telegram Bots API <https://core.telegram.org/bots/api>`_.                                               |
+------------------------+----------------------------------------------------------------------------------------------------------+
| Encoding               | Unicode.                                                                                                 |
+------------------------+----------------------------------------------------------------------------------------------------------+
| Content type           | Plaintext, markdown or HTML.                                                                             |
+------------------------+----------------------------------------------------------------------------------------------------------+
| Maximum content length | 4096 latin characters.                                                                                   |
+------------------------+----------------------------------------------------------------------------------------------------------+
| Emojis                 | Only in HTML.                                                                                            |
+------------------------+----------------------------------------------------------------------------------------------------------+
| Costs                  | None.                                                                                                    |
+------------------------+----------------------------------------------------------------------------------------------------------+

Telegram templates are similar to SMS templates.

.. hint:: Telegram requires you to have a ``telegram id`` as the address of the recipient.

    You can retrieve this ID by integrating a `Telegram Login Button <https://core.telegram.org/widgets/login>`_ on your website.

If you want to notify an event via Telegram, add the ``telegram`` folder within the event folder, and its
content into a text file named ``body`` within it::

    templates_base/
    └── mywebapp/
        └── password_changed/
            └── telegram/                 <- Telegram vector
                └── body                  <- content template

.. caution:: The Telegram platform poses some requirements to deliver messages!

    - `Create a Telegram Bot <https://core.telegram.org/bots/features#creating-a-new-bot>`_ that will send messages to your users.
