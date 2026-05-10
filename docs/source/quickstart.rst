.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

Quick start
===========

This guides you to:

1. :ref:`install <quickstart:install>` ``tattler`` into a virtual environment

2. :ref:`run <quickstart:run tattler server>` ``tattler_server``

3. :ref:`trigger a notification <quickstart:Send a notification>` through it -- via Python, ``curl``, or the bundled command-line tool.

4. Write your first :ref:`notification template <quickstart:Write your own notification templates>`.

5. Get faithful :ref:`live previews <quickstart:Get live previews while editing>` as you edit, with ``tattler_livepreview``.

6. :ref:`Organize your configuration <quickstart:Organize your configuration>`.

7. :ref:`Attach files to your notification <quickstart:Attach files to your notification>` -- inline images and regular files.

8. `Write an addressbook plug-in`_ to load contact data of your users.

9. `Write a context plug-in`_ to load common variables for your templates.

Install
-------

.. code-block:: bash

    # create and load a virtualenv to install into
    mkdir ~/tattler_quickstart
    python3 -m venv ~/tattler_quickstart/venv
    . ~/tattler_quickstart/venv/bin/activate

    # install tattler into it
    pip install tattler

Run tattler server
------------------

.. code-block:: bash

    export TATTLER_MASTER_MODE=production
    
    # if you need to customize your SMTP settings
    export TATTLER_SMTP_ADDRESS="127.0.0.1:25"
    export TATTLER_SMTP_AUTH="username:password" # you will learn secure configuration later
    export TATTLER_SMTP_TLS=yes

    # run tattler server on default 127.0.0.1:11503
    tattler_server

This causes the following basic scenario:

- ``tattler_server`` listens for requests on `<http://127.0.0.1:11503>`_.
- ``tattler_server`` delivers notification to the actual recipient (no dry-run!) due to the :ref:`TATTLER_MASTER_MODE <configuration:TATTLER_MASTER_MODE>` environment variable.
- ``tattler_server`` uses SMTP server ``127.0.0.1:25`` to deliver email, using STARTTLS and the given authentication credentials.

Don't worry, you'll soon learn a simpler, secure way to `manage this configuration <manage configuration>`_.

Send a notification
-------------------

You have three ways to trigger a notification: from Python (using tattler's
client SDK), via plain HTTP (e.g. ``curl``), or with the bundled
``tattler_notify`` command-line tool. All three hit the same REST endpoint
on ``tattler_server``.

Replace ``your@email.com`` with your actual email address, and pick the
flavor you prefer -- the rest of this guide will keep showing all three:

.. tab-set::

    .. tab-item:: Python
        :sync: python

        .. code-block:: python

            # in a terminal with the tattler venv loaded
            from tattler.client.tattler_py import send_notification

            send_notification('demoscope', 'demoevent', 'your@email.com',
                              mode='production')

    .. tab-item:: curl
        :sync: curl

        .. code-block:: bash

            # in any terminal
            curl -X POST 'http://127.0.0.1:11503/notification/demoscope/demoevent/?mode=production&user=your@email.com'

    .. tab-item:: command-line
        :sync: cli

        .. code-block:: bash

            # in a terminal with the tattler venv loaded
            tattler_notify -s '127.0.0.1:11503' -m production your@email.com demoscope demoevent

Here's what this does, regardless of the flavor you picked:

- It contacts ``tattler_server`` at its REST endpoint ``http://127.0.0.1:11503/notification/``.
- It asks to send the notification for ``demoevent``, which is built into tattler's distribution.
- It asks to send it to ``your@email.com``.
- It asks to actually send it to the indicated recipient, with mode ``production``.

In the terminal running ``tattler_server`` you'll see the notification go out successfully::

   INFO:tattler.server.tattler_utils:Sending demoevent:None (evname:language) to #your@email.com@email => [your@email.com], context={'user_id': 'your@email.com', 'user_email': 'your@email.com', 'user_sms': None, 'user_firstname': 'Your', 'user_account_type': None, 'user_language': None, 'correlation_id': 'tattler:b8357483-1115-4e8a-9b5e-4840cbd4a285', 'notification_id': '4840cbd4a285', 'notification_mode': 'production', 'notification_vector': 'email', 'notification_scope': 'demoscope', 'event_name': 'demoevent'} (cid=tattler:b8357483-1115-4e8a-9b5e-4840cbd4a285)
   INFO:tattler.server.sendable.vector_sendable:neb59232b-8819-4d2c-93f4-2791cda09f50: Sending 'demoevent'@'email' to: {'your@email.com'}
   INFO:tattler.server.tattlersrv_http:Notification sent. [{'id': 'email:fda614e8-61ef-4a00-98b6-6c993e90f1f0', 'vector': 'email', 'resultCode': 0, 'result': 'success', 'detail': 'OK'}]
   127.0.0.1 - - [11/Feb/2024 21:08:33] "POST /notification/demoscope/demoevent/?mode=production&user=your@email.com HTTP/1.1" 200 -

... and your mailbox will show the demo notification:


.. list-table::

    * - .. image:: ../../demos/tattler-notification-demo-email-html-light.png

      - .. image:: ../../demos/tattler-notification-demo-email-plaintext-light.png


Why demo? Why email?
^^^^^^^^^^^^^^^^^^^^

Now here's a couple of things which might turn your nose:

"Why ``demoevent``? I thought tattler allowed me to send my own notifications!"
    That's right. ``demoevent`` is a template built into tattler to allow demos. We'll look into writing your own notifications :ref:`soon <quickstart:Write your own notification templates>`.

"Why ``your@email.com``? I thought tattler would look up user information for me!"
    That's right. Tattler really shines when it loads your data for you. We'll look into that in the :ref:`plug-ins section <plugins/index:Tattler plug-ins>`.


Write your own notification templates
-------------------------------------

What actual content should tattler send, for the event we requested? :ref:`Event templates <keyconcepts/events:Notification events>` tell tattler that.

.. code-block:: bash

    # create a directory to host notification templates and change into it
    mkdir -p ~/tattler_quickstart/templates/mywebapp
    cd ~/tattler_quickstart/templates/mywebapp
    
    # create a template for an event titled "password changed"
    mkdir password_changed

    # we want event 'password_changed' to send an email notification
    mkdir password_changed/email
    cd password_changed/email
    # so we need a subject and body
    echo 'You successfully changed your password!' > subject.txt
    echo 'Hey!\n\nAccount password changed!' > body.txt

Done. Our notification templates directory now looks like this:

.. code-block:: text

    tattler_quickstart/
    └── templates/
       └── mywebapp/                 # scope  = mywebapp
           └── password_changed/     # event  = password_changed
               └── email/            # vector = email
                   ├── body.txt
                   └── subject.txt

Add an MJML template
^^^^^^^^^^^^^^^^^^^^

`MJML <https://mjml.io>`_ simplifies writing emails that render well across all email clients
despite their various HTML restrictions, including responsive layouts, and enables live previews.

Tattler supports MJML natively -- add a ``body.mjml`` file alongside your plain-text template:

.. code-block:: bash

    cd ~/tattler_quickstart/templates/mywebapp/password_changed/email

    cat > body.mjml << 'EOF'
    <mjml>
      <mj-body>
        <mj-section>
          <mj-column>
            <mj-text>
              <h1>Password changed!</h1>
              <p>Hey! Your account password was changed.</p>
            </mj-text>
          </mj-column>
        </mj-section>
      </mj-body>
    </mjml>
    EOF

Tattler compiles the MJML into responsive HTML at delivery time -- no extra tooling needed.

Your template directory now looks like this:

.. code-block:: text

    tattler_quickstart/
    └── templates/
       └── mywebapp/                 # scope  = mywebapp
           └── password_changed/     # event  = password_changed
               └── email/            # vector = email
                   ├── body.mjml     # MJML → compiled to HTML
                   ├── body.txt      # plain text fallback
                   └── subject.txt

Find more information about designing templates in the
:doc:`documentation for template designers <templatedesigners/index>`.

Get live previews while editing
-------------------------------

When editing email templates -- especially with :ref:`MJML <templatedesigners/email:MJML Emails>` or :ref:`HTML branding <templatedesigners/email:HTML Emails>` -- you usually want to iterate editing and previews.

Tattler gives you live, hi-fi email previews as you edit with its embedded ``tattler_livepreview`` tool:

.. code-block:: bash

    tattler_livepreview     ./tattler_quickstart/templates/

Simply give it your template base directory as first argument. ``tattler_livepreview`` guides you through some basic
configuration, and then sends you a notification as soon as it detected you modified a template file.

``tattler_livepreview`` is great because:

- It gives you reliable and faithful rendering through email, instead of deceiving browsers.

- It delivers you previews through the exact same tattler logic which you'll use in production, giving you free early testing e.g. for the consistency of your context data sets.

- It delivers via real SMTP, giving you a early headstart if your content looks spammy to your email provider -- a common case e.g. with Gmail.

Find more information in :doc:`Testing and live previews <testing/index>`.

Tell tattler server where to find event templates
-------------------------------------------------

``tattler_server`` takes the path holding notification event templates from the :ref:`TATTLER_TEMPLATE_BASE <configuration:TATTLER_TEMPLATE_BASE>` environment variable.
So let's restart it with it:

.. code-block:: bash

    # in the terminal which was running script 'tattler_server':
    
    # Stop the running instance with Ctrl-c

    # Re-start the instance with the new path
    TATTLER_TEMPLATE_BASE=~/tattler_quickstart/templates TATTLER_MASTER_MODE=production tattler_server

... and tell tattler to send a notification for your new event (replace your email address, as usual):

.. tab-set::

    .. tab-item:: Python
        :sync: python

        .. code-block:: python

            # in a terminal with the tattler venv loaded
            from tattler.client.tattler_py import send_notification

            send_notification('mywebapp', 'password_changed', 'your@email.com',
                              mode='production')

    .. tab-item:: curl
        :sync: curl

        .. code-block:: bash

            curl -X POST 'http://127.0.0.1:11503/notification/mywebapp/password_changed/?user=your@email.com&mode=production'

    .. tab-item:: command-line
        :sync: cli

        .. code-block:: bash

            tattler_notify -m production your@email.com mywebapp password_changed

Upon which ``tattler_server`` will confirm::

    INFO:tattler.server.tattler_utils:Sending password_changed:None (evname:language) to #your@email.com@email => [your@email.com], context={'user_id': 'your@email.com', 'user_email': 'your@email.com', 'user_sms': None, 'user_firstname': 'user', 'user_account_type': None, 'user_language': None, 'correlation_id': 'tattler:a6c81356-662a-4b1a-a6ca-a0b9dbcbe34e', 'notification_id': 'a0b9dbcbe34e', 'notification_mode': 'production', 'notification_vector': 'email', 'notification_scope': 'mywebapp', 'event_name': 'password_changed'} (cid=tattler:a6c81356-662a-4b1a-a6ca-a0b9dbcbe34e)
    INFO:tattler.server.sendable.vector_sendable:n83311a12-f922-400b-8bef-362a84289f9e: Sending 'password_changed'@'email' to: {'your@email.com'}
    INFO:tattler.server.tattlersrv_http:Notification sent. [{'id': 'email:56985c3c-b5c9-4c87-8329-75c2335d28de', 'vector': 'email', 'resultCode': 0, 'result': 'success', 'detail': 'OK'}]
    127.0.0.1 - - [11/Feb/2024 21:33:55] "POST /notification/mywebapp/password_changed/?user=your@email.com&mode=production HTTP/1.1" 200 -

Then go check your mailbox to confirm that you received the notification with the content you put into your template.

.. hint:: Exploit the demo template!

    The demo template you used earlier is your friend. It includes tips on writing effective,
    portable email notifications -- and most of all it includes some code snippets which you can
    simply copy and paste to write your own templates.

    Find the source code of the demo templates in
    `tattler's repository <https://github.com/tattler-community/tattler-community/blob/main/src/tattler/templates/demoscope/demoevent>`_.

Organize your configuration
---------------------------

Tattler uses environment variables for configuration as they are highly flexible and avoid
overbloating code with parsers.

`envdir <https://envdir.readthedocs.io>`_ comes to your rescue to organize configuration cleanly,
maintainably and securely. Envdir loads environment variables from a directory that holds one file
per configuration key, whose content is the configuration value.

Here's how you setup your configuration using ``envdir``:

.. code-block:: bash

    # create the directory holding your configuration, and change into it
    mkdir -p ~/tattler_quickstart/etc
    cd ~/tattler_quickstart/etc

    # create file "TATTLER_MASTER_MODE" to hold content "staging",
    # to have tattler copy notifications to the actual recipient and to NOTIF_DEBUG_RECIPIENT_EMAIL
    echo "staging" > TATTLER_MASTER_MODE

    # add more non-sensitive configuration values
    echo support@myorganization.org > TATTLER_EMAIL_SENDER
    echo "127.0.0.1:11503" > TATTLER_LISTEN_ADDRESS
    echo ~/tattler_quickstart/templates > TATTLER_TEMPLATE_BASE
    echo "your_own_email@company.com" > NOTIF_DEBUG_RECIPIENT_EMAIL
    echo "127.0.0.1:25" > TATTLER_SMTP_ADDRESS
    echo yes > TATTLER_SMTP_TLS
    
    # And here is how to add sensitive configuration values:

    # 1. create a file and restrict access to it
    touch TATTLER_SMTP_AUTH
    chown tattler TATTLER_SMTP_AUTH
    chmod 0400 TATTLER_SMTP_AUTH
    # 2. add content using an editor, so it does not get stored into your shell history
    vim TATTLER_SMTP_AUTH

And finally start tattler having ``envdir`` loads the configuration above:

.. code-block:: bash

    # load the virtualenv where you installed tattler
    . ~/tattler_quickstart/venv/bin/activate

    # have envdir load the configuration into an environment where tattler is started
    envdir ~/tattler_quickstart/etc tattler_server &

Refer to :doc:`available configuration options <configuration>`
and :doc:`documentation for sysadmins <sysadmins/index>` for further information.


Attach files to your notification
---------------------------------

Email notifications can carry **inline images** (a logo embedded in the body)
and **regular file attachments** (e.g. a PDF invoice the recipient can download).

Tattler tells the two apart by the dictionary key you use:

* a key containing ``@`` is the *Content-ID* of an inline image, referenced
  from the HTML body as ``<img src="cid:NAME">``.
* a key without ``@`` is the *filename* of a regular paperclip attachment;
  its extension drives the MIME type.

Reference an inline image from your template
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open the ``body.mjml`` you wrote earlier and add an ``<mj-image>`` pointing
at the cid you'll attach below:

.. code-block:: xml

    <mjml>
      <mj-body>
        <mj-section>
          <mj-column>
            <mj-image src="cid:logo@brand" width="120px"/>
            <mj-text>
              <h1>Password changed!</h1>
              <p>Hey! Your account password was changed.</p>
            </mj-text>
          </mj-column>
        </mj-section>
      </mj-body>
    </mjml>

Trigger a notification with attachments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Python SDK takes attachments through a dedicated ``attachments`` keyword
and accepts :class:`pathlib.Path` (local file, the SDK reads and base64-encodes
it for you) or an ``http(s)://`` URL string (tattler fetches it server-side).

Over plain HTTP, attachments travel under the reserved ``_attachments`` key
in the JSON body, where each entry takes either a ``url`` or a ``content_b64``
(base64 of the file bytes):

.. tab-set::

    .. tab-item:: Python
        :sync: python

        .. code-block:: python

            from pathlib import Path
            from tattler.client.tattler_py import send_notification

            send_notification(
                'mywebapp', 'password_changed', 'your@email.com',
                mode='production',
                attachments={
                    'logo@brand': Path('/path/to/logo.png'),               # local file
                    'terms.pdf':  'https://yourdomain.example/terms.pdf',  # remote URL
                },
            )

    .. tab-item:: curl
        :sync: curl

        .. code-block:: bash

            curl -X POST \
                -H 'Content-Type: application/json' \
                -d '{
                      "_attachments": {
                        "logo@brand": {"url": "https://yourdomain.example/logo.png"},
                        "terms.pdf":  {"url": "https://yourdomain.example/terms.pdf"}
                      }
                    }' \
                'http://127.0.0.1:11503/notification/mywebapp/password_changed/?user=your@email.com&mode=production'

    .. tab-item:: command-line
        :sync: cli

        .. code-block:: bash

            # repeat -a for each file; use NAME@... for inline images, plain
            # filenames for paperclip attachments
            tattler_notify -m production your@email.com mywebapp password_changed \
                -a 'logo@brand=/path/to/logo.png' \
                -a 'terms.pdf=https://yourdomain.example/terms.pdf'

Your inbox now shows the inline logo rendered in the email body and the PDF
attached as a paperclip.

Total attachments per email are capped at 7 MB. Find the full reference
-- MIME-type detection rules, the trust model and the underlying wire
format -- in :ref:`Sending attachments <developers/api_http:Sending attachments>`.


Write an addressbook plug-in
----------------------------

An addressbook plug-in enables tattler to automatically retrieve contact data about your users.

Once you have this, your applications no longer need to provide contact data to notify users.

They simply tell tattler "notify user #123 about event X", and tattler figures out who is ``123``,
what vectors it provided (email address, phone number), what are the concrete addresses, etc.

Start by creating a directory to hold your plugin(s):

.. code-block:: bash

    # create directory to hold tattler plug-ins
    mkdir -p ~/tattler_quickstart/plugins
    cd ~/tattler_quickstart/plugins

    # start editing your addressbook plug-in
    vim myaddressbook_tattler_plugin.py

You may fill your plugin file ``myaddressbook_tattler_plugin.py`` starting from the 
`sample addressbook plugin <https://github.com/tattler-community/tattler-community/blob/main/plugins/sqladdressbook_tattler_plugin.py>`_
in tattler's repository. Just replace the names of your tables and fields to your own schema:

.. literalinclude:: ../../plugins/sqladdressbook_tattler_plugin.py

Now enable tattler to load the plugin:

.. code-block:: bash

    # load the virtualenv where you installed tattler
    cd ~/tattler_quickstart
    . venv/bin/activate

    # install the dependencies required by your plug-in. In this case, let's assume
    # sqlalchemy
    pip install sqlalchemy

    # use the sample database from our codebase to test this
    curl -O https://raw.githubusercontent.com/tattler-community/tattler-community/main/plugins/sqlplugins.sql
    sqlite3 sqlplugins.db < sqlplugins.sql
    # check out the content of the sample DB. Feel free to replace e.g. your email address
    sqlite3 sqlplugins.db 'select * from auth_user join userprofile on auth_user.id = user_id'

    # configure tattler to load your new plug-in
    echo ~/tattler_quickstart/plugins/ > ~/tattler_quickstart/etc/TATTLER_PLUGIN_PATH
    echo sqlite:////$HOME/tattler_quickstart/sqlplugins.db > ~/tattler_quickstart/etc/DATABASE

    # you may want to enable debug-level logging when testing new logic
    echo debug > ~/tattler_quickstart/etc/LOG_LEVEL

    # set email address to have tattler use as sender
    echo support@myorganization.org > TATTLER_EMAIL_SENDER

    # set tattler in 'staging' mode, i.e. copy every notification to a 'supervisor' address
    echo staging > TATTLER_MASTER_MODE
    
    # set email address to have tattler copy every notification to ()
    echo notification@myorganization.org > TATTLER_SUPERVISOR_RECIPIENT_EMAIL
    
    # restart tattler_server with the new configuration
    envdir ~/tattler_quickstart/etc tattler_server

Have a look at the log output here. You'll see some message like the following::

    ...
    INFO:tattler.server.pluginloader:Loading plugin SQLAddressbookPlugin (<class 'myaddressbook_tattler_plugin.SQLAddressbookPlugin'>) from module myaddressbook_tattler_plugin
    ...

and now trigger a notification using a user ID:

.. tab-set::

    .. tab-item:: Python
        :sync: python

        .. code-block:: python

            from tattler.client.tattler_py import send_notification

            send_notification('demoscope', 'demoevent', '2', mode='production')

    .. tab-item:: curl
        :sync: curl

        .. code-block:: bash

            curl -X POST 'http://127.0.0.1:11503/notification/demoscope/demoevent/?user=2&mode=production'

    .. tab-item:: command-line
        :sync: cli

        .. code-block:: bash

            tattler_notify -m production 2 demoscope demoevent

... and there you go: tattler delivers the notification to email address ``your@email.net`` as stored in the database::

    INFO:tattler.server.pluginloader:Looking up recipient 2 with addressbook plugin #1 'SQLAddressbookPlugin'
    # ..
    DEBUG:tattler.server.tattler_utils:Contacts for recipient 2 are: {'email': 'your@email.net', 'first_name': 'Michelle', 'mobile': '+1789456321', 'telegram': '5689234578', 'sms': '+1789456321', 'whatsapp': '+1789456321'}
    INFO:tattler.server.tattler_utils:Recipient 2 is reachable over 1 vectors of the 1 requested: {'email'}

More details on this in :ref:`addressbook plug-in documentation <plugins/addressbook:Addressbook plug-ins>`.


Write a context plug-in
-----------------------

A context plug-in enables tattler to automatically retrieve data to make available to all your templates.

Once you have this, your applications no longer need to collect and supply data to expand templates.
Instead, tattler autonomously pre-loads the necessary data through your context plug-in.

They are called "context" because they provide additional context to expand templates with,
i.e. a collection of additional variables that templates may access.

Create your context plug-in in the same plug-in folder you created previously:

.. code-block:: bash

    # as created in the example before
    cd plugins

    # start editing your context plug-in
    vim mycontext_tattler_plugin.py

Feel free to fill your plugin file ``mycontext_tattler_plugin.py`` starting from the
`sample context plugin <https://github.com/tattler-community/tattler-community/blob/main/plugins/sqlcontext_tattler_plugin.py>`_
in tattler's repository. Just replace the names of your tables and fields to your own schema:

.. literalinclude:: ../../plugins/sqlcontext_tattler_plugin.py

How to enable the new plug-in? If you already followed `Write an addressbook plug-in`_ ,
you have already setup what's needed. If not, go do so 🙂

Then simply reload tattler and you'll see the new plug-in loaded::

    INFO:tattler.server.pluginloader:Loading plugin SQLContextTattlerPlugin (<class 'sqlcontext_tattler_plugin.SQLContextTattlerPlugin'>) from module sqlcontext_tattler_plugin

and now trigger a notification again:

.. tab-set::

    .. tab-item:: Python
        :sync: python

        .. code-block:: python

            from tattler.client.tattler_py import send_notification

            send_notification('demoscope', 'demoevent', '2', mode='production')

    .. tab-item:: curl
        :sync: curl

        .. code-block:: bash

            curl -X POST 'http://127.0.0.1:11503/notification/demoscope/demoevent/?user=2&mode=production'

    .. tab-item:: command-line
        :sync: cli

        .. code-block:: bash

            tattler_notify -m production 2 demoscope demoevent

... and observe that tattler loads new context variables::

    INFO:tattler.server.pluginloader:Context after plugin SQLContextTattlerPlugin (in 0:00:00.002836): {'user_id': '2', 'user_email': 'your@email.net', 'user_sms': '+1789456321', 'user_firstname': 'Your', 'user_account_type': 'unknown', 'user_language': None, 'correlation_id': 'tattler:af4054ab-fac7-4b3a-ad80-0a9fa4326d36', 'notification_id': '0a9fa4326d36', 'notification_mode': 'debug', 'notification_vector': 'email', 'notification_scope': 'mywebapp', 'event_name': 'password_changed', 'traffic': 1224994602, 'invoice': [['2023123001', True]]}

More details on this in :ref:`context plug-in documentation <plugins/context:Context plug-ins>`.


Done!
-----

You have gotten to know most of Tattler's capabilities already 👏🏻

If this journey scratched your itch, consider giving a `star to our repo <https://github.com/tattler-community/tattler-community>`_.
And if you run a tech blog -- would Tattler possibly be a suitable next topic?

If you found friction at any step of the way, do `let us know <mailto:docs@tattler.dev>`_. We take documentation seriously and look forward for feedback!
