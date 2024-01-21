Email templates
---------------

+------------------------+---------------------------------------------------------------------------------+
| Address type           | Regular e-mail address.                                                         |
+------------------------+---------------------------------------------------------------------------------+
| Default gateway        | Your SMTP server. Or your ISP's. Or 3\ :sup:`rd`-party ones.                    |
+------------------------+---------------------------------------------------------------------------------+
| Encoding               | ASCII                                                                           |
+------------------------+---------------------------------------------------------------------------------+
| Content type           | HTML and/or plaintext.                                                          |
+------------------------+---------------------------------------------------------------------------------+
| Maximum content length | Several MegaBytes.                                                              |
+------------------------+---------------------------------------------------------------------------------+
| Emojis                 | Yes.                                                                            |
+------------------------+---------------------------------------------------------------------------------+
| Costs                  | None.                                                                           |
+------------------------+---------------------------------------------------------------------------------+


Read :ref:`SMS templates <templatedesigners/sms:SMS templates>` first as this builds upon it.

An email has multiple parts at play:

- a subject
- a body
- potentially a HTML version of the body
- potentially a priority

Email templates collect each of those parts in a separate template file. All
such files are enclosed into an ``email`` folder::

    templates_base/
    └── mywebapp/                       <-- a scope
        └── password_changed/           <- an event
            └── email/                  <- email vector
                ├── subject             <- mandatory
                ├── body_plain          <- mandatory
                ├── body_html
                └── priority

.. hint:: The ``body_plain`` definition is not required in `Tattler's enterprise edition <https://tattler.dev/#enterprise>`_.

    Tattler enterprise edition includes the :ref:`auto-text <templatedesigners/autotext:auto-text>` feature, which allows
    you to only provide ``body_html``.
    
The files have the following purpose:

``subject``
    Mandatory. Contains template text which will be expanded with template variables to generate the subject of the email to send.

``body_plain``
    Mandatory (in Tattler community edition). Contains template text which will be expanded with template variables to generate the body of the email to send.
    This is the plain-text body standard in every email. If a ``body_html`` file is also provided, this content only serves as a "fallback" for recipients who lack support for HTML emails.

``body_html``
    Optional. Contains template text which will be expanded with template variables to generate the HTML version of the email to send. If the recipient's e-mail application supports HTML emails, they will
    view this content first.

``priority``
    Optional. Contains an integer ∈ { 1, 2, 3, 4, 5 }, where ``1`` is "highest" and ``3`` is "normal" priority.
    Priority is implemented by setting the ``X-Priotity`` header in the final email to the user,
    so its potency depends on whether the user's email application supports that attribute -- which many do.

HTML Emails
-----------

HTML emails are plain-text emails with an HTML file attached.

Your job is to write the template for that HTML file.

Tattler's job is to expand the template and assemble the email with subject,
plain-text part and HTML part.

Write the HTML template into file ``body_html``. Make it valid HTML enclosed in
a ``<html></html>`` element:

.. code-block:: html

    <!-- this is the content of file body_html -->
    <html>
        <body>
            <h1>Password changed!</h1>

            <p>Dear {{ user_firstname }},</p>

            <p>Someone (presumably you) changed the password to your account today at  {{ appointment_time }}.</p>
        </body>
    </html>

Hold your HTML
^^^^^^^^^^^^^^

Tattler supports all the HTML you want, but email clients don't.

Some email clients don't support HTML at all -- in which case your recipient will only see
the content you prepared in ``body_plain``.

Clients that do support HTML emails do so limitedly and inconsistently.

Avoid JavaScript. Basic CSS is often supported. Refer to the excellent
`CanIEmail <https://www.caniemail.com>`_.


Email priority
--------------

Many email clients support setting and viewing an email *priority*.

These include Thunderbird, Gmail, Outlook and Apple mail.

tattler allows you to set an email's priority by placing the ``priority`` file
into the email template folder:

.. code-block:: bash

    cd templates_base/password_changed/email/
    echo "1" > priority

This will make the message "high-priority" when the user's email application supports
the feature.

Setting this file makes sense with only 2 values:

* ``1`` for "high priority"
* ``5`` for "low priority"

Value ``3`` (normal priority) is a non-action, and the values inbetween are not meaningful.

Setting messages as high-priority raises the visibility of the notification in the user's mailbox,
which loads notification fatigue even further -- so use it sparingly. A case where high-priority
makes sense is when the notification is important and also time-critical action.

