Live previews
=============

.. tip:: ``tattler_preview`` only assists with email notifications, not SMS / WhatsApp / Telegram.

    You may define any number of additional vectors in your event templates, but ``tattler_livepreview``
    will only monitor and deliver email templates.

Tattler includes tool ``tattler_livepreview`` which emails you live previews of your templates as you edit them.

Run this from the command line as follows:

.. code-block:: bash
    
    tattler_livepreview     ./tattler_quickstart/templates/
    #                       |--- path of template base ---|

It takes as argument a path to a :ref:`template base <templatedesigners/structure:Overall template structure>` directory,
which must be structured as such.

It guides you through a setup step, then monitors your templates and delivers them whenever they are changed.


Configuration
-------------

When started, ``tattler_livepreview`` prompts you for some basic configuration:

1. Which email address to send "preview" notifications to? (Required)

2. Which email address to use as "From" for preview notifications? (Optional)

3. Which SMTP server to deliver preview notifications through. (Required)

4. Which SMTP credentials to authenticate with. (Optional)

This configuration is saved into a `configuration envdir <https://envdir.readthedocs.io>`_.

In subsequent runs, ``tattler_livepreview`` still asks you for those settings, but offers you
the values you entered in the latest run as default -- so you can simply "Enter" you way through it.


Notes on SMTP server
^^^^^^^^^^^^^^^^^^^^

Use your own SMTP server if you have one.

If you don't, simply enter ``gmail`` when ``tattler_livepreview`` asks you for the SMTP server address.

``tattler_livepreview`` will self-configure for gmail, then guide you through Gmail's requirement for delivery.

Google requires the following to allow you access to their SMTP server:

- To have recently logged into your google account from the current device. Log-out and log back in to make sure this requirement is satisfied.

- If your google account has 2-factor authentication enabled, google requires you to setup an `App Password <https://myaccount.google.com/apppasswords>`_ to use in place of your actual password as SMTP login credentials.


Configuration privacy
^^^^^^^^^^^^^^^^^^^^^

If your SMTP server requires login credentials, ``tattler_livepreview`` will store them
as part of the configuration.

``tattler_livepreview`` arranges this configuration so as to forbid access to other users on this machine.
Additionally, the content is obfuscated to prevent applications running with the same user from trivially
accessing it.

Still, beware that this is no encryption. Encryption would force you to type in a decryption password
every time you run ``tattler_livepreview``, defeating the purpose of storing those items.

That's enough security for most. If it isn't for you, simply remove the configuration
folder used by ``tattler_livepreview`` as soon as you're done configuring it.


Passing variables
-----------------

Your templates will often contain variables or custom logic like loops and conditionals.

``tattler_livepreview`` allows you to pass data into your template to test this logic.

Simply provide a file named ``context.json`` into the event template directory:

.. code-block::

    tattler_quickstart/
    └── templates/
       └── mywebapp/                    # scope
           └── reservation_confirmed/   # event
               ├── context.json         # <-- custom context 
               └── email/
                   ├── body.txt
                   └── subject.txt

This file must contain a JSON object, with zero or more keys:

.. code-block:: JSON

    {
        "consultants": [
            "John Doe",
            "Lady Jane"
        ],
        "appointment": {
            "timestamp": "2024-05-11T10:45:04.123",
            "location": {
                "latitude": 47.6589151,
                "longitude": 9.1790431
            },
            "parking_available": false,
        }
    }

Notice the following in the example:

- There may be only one "root" element, and it must be an object.

- Keys of the object expand to the variable names in your template.

- Values may have any format -- even be structured. Their data type and format is only determined by what your templates expect it to be.

- ``tattler`` automatically detects strings formatted as ISO-8601 and converts them into a python datetime. (field ``timestamp`` in the example)
