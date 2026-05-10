Manual testing
==============

:ref:`Live previews <testing/livepreview:Live previews>` is the recommended
way to develop your templates.

However, you might occasionally want to fire a single notification manually.

You can do so with ``tattler_notify``.

Send your template
------------------

Use ``tattler_notify`` to get Tattler to send the template:

.. code:: bash

    # send event 'password_changed' in scope 'mywebapp' to 'your@email.con'
    tattler_notify --mode production your@email.com mywebapp password_changed

Pass context variables
^^^^^^^^^^^^^^^^^^^^^^

If your template requires some variables (context), you may pass them as follows:

.. code:: bash

    # some simple context variables 'foo' and 'bar'
    tattler_notify --mode production your@email.com mywebapp password_changed foo=1 'bar=Some name'

Beware of shell expansion! Quote variables whose value includes whitespace, or shell symbols like '$'.

You may also pass context variables via JSON file. Do this if your template requires complex variables like objects:

.. code:: bash

    # pass context variables via JSON file, which must contain a dictionary, i.e. a JSON object at its root.
    tattler_notify --mode production --json-context ctx_password_changed.json your@email.com mywebapp password_changed

You may also combine both forms: if you pass a JSON context file and also some variables on the command line,
the command line variables will complement (or override!) the former.

This allows you to quickly change specific values on top of a base context.

Attach a file
^^^^^^^^^^^^^

For email notifications, you can attach files with ``--attach NAME=VALUE`` (repeatable):

.. code:: bash

    # attach an invoice from disk and an inline logo
    tattler_notify --mode production your@email.com mywebapp invoice_ready \
        --attach invoice.pdf=/tmp/inv.pdf \
        --attach logo@brand=/srv/branding/logo.png

    # have the server fetch a file from a URL
    tattler_notify --mode production your@email.com mywebapp policy_update \
        --attach terms.pdf=https://internal/legal/terms.pdf

The shape of ``NAME`` decides how the file is treated:

* ``NAME`` containing ``@`` (e.g. ``logo@brand``) is the **Content-ID** of an
  inline image, referenced from the HTML template as
  ``<img src="cid:logo@brand">``.
* ``NAME`` without ``@`` is the **filename** of a regular paperclip-style
  attachment shown in the recipient's mail client.

The shape of ``VALUE`` decides where the bytes come from:

* A bare path (e.g. ``/tmp/inv.pdf``) -- the client reads the local file and
  uploads it.
* An ``http(s)://`` URL -- the server fetches it.

See :ref:`Sending attachments <developers/api_http:Sending attachments>` for the
full schema, MIME-detection rules, size limits, and trust model.

Need a server for testing?
--------------------------

To start an instance of ``tattler_server``, you usually want to set the following config items:

- The SMTP server to send mail through.
- The templates directory.
- Potentially a higher LOG_LEVEL.

Here's how you do that:

.. code:: bash

    mkdir tattler_conf
    cd tattler_conf

    # set relevant config keys
    echo ~/myproject/notifications/templates > TATTLER_TEMPLATE_BASE
    echo smtp.gmail.com:465                  > TATTLER_SMTP_ADDRESS
    echo yes                                 > TATTLER_SMTP_TLS
    touch TATTLER_SMTP_AUTH
    chmod 400 TATTLER_SMTP_AUTH
    vim TATTLER_SMTP_AUTH # add username:password into it

    # run it
    envdir tattler_conf tattler_server

Keep in mind that :ref:`tattler_livepreview <testing/livepreview:Live previews>` does all of
this for you. It uses the same setup to faithfully reproduce the behavior during production.

Because of that, running server and client manually is a rare necessity.
