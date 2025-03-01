Base configuration
------------------

Tattler is configured via environment variables.

Start by providing the following basic ones:

- :ref:`TATTLER_TEMPLATE_BASE <configuration:TATTLER_TEMPLATE_BASE>` -- where tattler will look for :ref:`event templates <keyconcepts/events:event templates>` to send.
- :ref:`TATTLER_DEBUG_RECIPIENT_EMAIL <configuration:TATTLER_DEBUG_RECIPIENT_*>` -- to what email address tattler should send any notification fired during this testing time, instead of the real recipient.
- :ref:`TATTLER_MASTER_MODE <configuration:TATTLER_MASTER_MODE>` -- whether to divert notifications to a debug address, or to send them to the real recipient.

As the number of variable grows, you'll get uncomfortable with a long command-line.

And that becomes critical once you want to pass sensitive data, such as database access credentials,
potentially for your own :ref:`plug-ins <plugins/index:Tattler plug-ins>`.

To clean that up, wrap all configuration variables into an `envdir <https://pypi.org/project/envdir/>`_:

.. code-block:: bash

    # change to tattler user
    sudo -s tattler

    # load the virtual environment
    . ~tattler/venv_tattler/bin/activate

    # install 'envdir' to manage envvar-based configurations
    pip install envdir

    # create an envdir for a 'testing' environment
    mkdir -p ~tattler/confenv/testing

    # fill variables into it
    cd ~tattler/confenv/testing

    echo "debug" > TATTLER_MASTER_MODE
    echo "127.0.0.1:11503" > TATTLER_LISTEN_ADDRESS
    echo "~tattler/tattler_templates" > TATTLER_TEMPLATE_BASE
    echo "your_own_email@company.com" > NOTIF_DEBUG_RECIPIENT_EMAIL

    # for any private configuration value:
    touch DATABASE
    chmod 400 DATABASE
    vim DATABASE    # ... and paste the value manually

    # when your envdir is done, start tattler with it
    envdir ~tattler/confenv/testing tattler_server

Go through the :ref:`configuration reference <configuration:Configuration for tattler_server>` for the full list of your options.

