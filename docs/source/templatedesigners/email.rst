Email templates
===============

+------------------------+---------------------------------------------------------------------------------+
| Address type           | Regular e-mail address.                                                         |
+------------------------+---------------------------------------------------------------------------------+
| Default gateway        | Your SMTP server. Or your ISP's. Or 3\ :sup:`rd`-party ones.                    |
+------------------------+---------------------------------------------------------------------------------+
| Encoding               | ASCII                                                                           |
+------------------------+---------------------------------------------------------------------------------+
| Content type           | MJML, HTML and/or plain text.                                                   |
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
                ├── subject.txt         <- mandatory
                ├── body.txt            <- mandatory
                ├── body.html           <- or body.mjml
                └── priority.txt

.. hint:: The ``body.txt`` definition is not required in `Tattler's enterprise edition <https://tattler.dev/#enterprise>`_.

    Tattler enterprise edition includes the :ref:`auto-text <templatedesigners/autotext:auto-text>` feature, which allows
    you to only provide ``body.html``.
    
The files have the following purpose:

``subject.txt``
    Mandatory. Contains template text which will be expanded with template variables to generate the subject of the email to send.

``body.txt``
    Mandatory (in Tattler community edition). Contains template text which will be expanded with template variables to generate the body of the email to send.
    This is the plain-text body standard in every email. If a ``body.html`` file is also provided, this content only serves as a "fallback" for recipients who lack support for HTML emails.

``body.html``
    Optional. Contains template text which will be expanded with template variables to generate the HTML version of the email to send. If the recipient's e-mail application supports HTML emails, they will
    view this content first.

``body.mjml``
    Optional. Alternative to ``body.html`` -- provide one or the other, not both. Contains `MJML <https://mjml.io>`_ markup
    which tattler automatically compiles into HTML before delivering. See :ref:`MJML Emails <templatedesigners/email:MJML Emails>` below.

``priority.txt``
    Optional. Contains an integer ∈ { 1, 2, 3, 4, 5 }, where ``1`` is "highest" and ``3`` is "normal" priority.
    Priority is implemented by setting the ``X-Priotity`` header in the final email to the user,
    so its potency depends on whether the user's email application supports that attribute -- which many do.

MJML or HTML?
-------------

Tattler supports two ways to write rich email templates: MJML and HTML.

Use **MJML** if you want to:

- Avoid dealing with the quirks of email HTML rendering (inconsistent CSS support, broken layouts, etc.).
- Get responsive emails that render well across all email clients without extra effort.
- Write clean, readable markup and let the compiler handle the cross-client workarounds.
- Get instant :ref:`browser-based previews <testing/livepreview:Browser-based previews with MJML>` as you edit, using the MJML VS Code extension or online editor.

Use **HTML** if you:

- Already have existing HTML email templates you want to reuse.
- Need precise control over every element in the final HTML output.
- Depend on HTML constructs not yet supported by `mjml-python <https://pypi.org/project/mjml/>`_.

Both approaches support Jinja template variables, :ref:`base templates <templatedesigners/base_templates:Base templates>`,
and :ref:`live previews <testing/livepreview:Live previews>`.

.. warning::

    Providing either ``body.html`` or ``body.mjml`` (or neither) in any event. Tattler's template validation at startup
    will report an error if both files exist for an event.

MJML Emails
------------

Writing HTML emails that render correctly across email clients is notoriously difficult.
`MJML <https://mjml.io>`_ is a markup language that abstracts away these inconsistencies
and compiles into responsive, cross-client HTML.

Tattler supports MJML natively. Provide a ``body.mjml`` file with your MJML markup::

    templates_base/
    └── mywebapp/
        └── password_changed/
            └── email/
                ├── subject.txt
                ├── body.txt
                └── body.mjml

Tattler compiles the MJML into HTML at delivery time, so you write clean, semantic markup
and get reliable rendering across email clients for free.

Use Jinja template variables in your MJML just as you would in any other tattler template:

.. code-block:: html

    <mjml>
      <mj-body>
        <mj-section>
          <mj-column>
            <mj-text>
              <h1>Password changed!</h1>
              <p>Dear {{ user_firstname }},</p>
              <p>Your password was changed at {{ appointment_time }}.</p>
            </mj-text>
          </mj-column>
        </mj-section>
      </mj-body>
    </mjml>

Tattler relies on `mjml-python <https://pypi.org/project/mjml/>`_ for compilation,
not the official node-based MJML compiler -- so support for some corners of the language
may lag behind the official compiler.

HTML Emails
-----------

If you prefer to write HTML directly, you can provide a ``body.html`` file instead of ``body.mjml``.

HTML emails are plain-text emails with an HTML file attached, packaged in a special way dictated by the `MIME standard <https://de.wikipedia.org/wiki/Multipurpose_Internet_Mail_Extensions>`_.

Tattler takes care of this special packaging, so your job is to write the template for that HTML file.

Write the HTML template into file ``body.html``. Make it valid HTML enclosed in
a ``<html></html>`` element:

.. code-block:: html

    <!-- this is the content of file body.html -->
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
the content you prepared in ``body.txt``.

Clients that do support HTML emails do so limitedly and inconsistently.

Avoid JavaScript. Basic CSS is often supported. Refer to the excellent
`CanIEmail <https://www.caniemail.com>`_.

MJML abstracts away most of these concerns -- see :ref:`MJML or HTML? <templatedesigners/email:MJML or HTML?>` above.


Email priority
--------------

Many email clients support setting and viewing an email *priority*.

These include Thunderbird, Gmail, Outlook and Apple mail.

tattler allows you to set an email's priority by placing the ``priority.txt`` file
into the email template folder:

.. code-block:: bash

    cd templates_base/password_changed/email/
    echo "1" > priority.txt

This will make the message "high-priority" when the user's email application supports
the feature.

Setting this file makes sense with only 2 values:

* ``1`` for "high priority"
* ``5`` for "low priority"

Value ``3`` (normal priority) is a non-action, and the values in-between are not meaningful.

Setting messages as high-priority raises the visibility of the notification in the user's mailbox,
which loads notification fatigue even further -- so use it sparingly. A case where high-priority
makes sense is when the notification is important and also time-critical action.

