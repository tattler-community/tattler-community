System administrators
=====================

Your role:

- Install, configure, and run tattler.
- Keep it secure, including software updates.
- Keep it running.
- Keep it reachable by other systems.
- Deploy templates provided by :ref:`template designers <roles:template designers>`, or provide them with a way to do so themselves.
- Provision plug-ins if any is required.

Components
----------

A tattler deployment looks like this:

.. mermaid::

    C4Context
    title Container diagram for Tattler
    Person(TemplDev, "Template developer", "Implements graphical<br/>and voice brand.")
    Person(SWDev, "Software Developer", "Codes systems which,<br/>trigger notifications")
    System_Boundary(TattlerCont, "Tattler container") {
        System(Tattler, "Tattler", "Sends notifications<br/>over various vectors.")
        SystemDb_Ext(TattlerTempl, "Notification templates", "Text and style to deliver.")
        System_Ext(TattlerPlugins, "Custom plug-ins", "Look up user contacts<br/>and other data.")
        Rel(Tattler, TattlerTempl, "Loads from")
        Rel(Tattler, TattlerPlugins, "Loads info from")
        Rel(SWDev, TattlerPlugins, "Develops and maintains.")
    }
    Rel(TemplDev, TattlerTempl, "Writes")
    Rel(SWDev, BookingSys, "Develops and maintains.")
    System_Boundary(Client_Sys, "Client system") {
        System_Ext(BookingSys, "Booking System", "Manages reservations by users.")        
    }
    Rel(BookingSys, Tattler, "Request to notify")


Deployment path
---------------

We proceed as follows:

1. Install into a virtual environment.

2. Provide a base configuration.

3. Provide access to template designers.

4. Deploy custom plug-ins.

5. Deploy into an own container.

6. Upgrade without downtime.


Install on the bare system
--------------------------

This is suboptimal, but start here and then build up better deployment approaches on a solid foundation.

.. code-block:: bash

    # create a user for tattler and change to it
    adduser tattler
    sudo -s tattler

    # build a python virtual environment
    python3 -m venv ~tattler/venv_tattler

    # load the virtual environment
    . ~tattler/venv_tattler/bin/activate

    # install tattler (with Jinja template engine) into the new venv
    pip install 'tattler[Jinja]'

    # deploy templates
    mkdir ~tattler/tattler_templates

    # run tattler
    NOTIF_DEBUG_RECIPIENT_EMAIL=your_own_email@company.com \
        TATTLER_TEMPLATE_BASE=~tattler/tattler_templates \
        TATTLER_LISTEN_ADDRESS="127.0.0.1:11503" \
        TATTLER_MASTER_MODE="debug" \
        tattler_server

At this point, tattler will be listening on ``127.0.0.1:11503`` for requests to notify.


Base configuration
------------------

Tattler is configured via environment variables.

Start by providing the following basic ones:

- :ref:`TATTLER_TEMPLATE_BASE <configuration:TATTLER_TEMPLATE_BASE>` -- where tattler will look for :ref:`event templates <keyconcepts:event templates>` to send.
- :ref:`TATTLER_DEBUG_RECIPIENT_EMAIL <configuration:TATTLER_DEBUG_RECIPIENT_*>` -- to what email address tattler should send any notification fired during this testing time, instead of the real recipient.
- :ref:`TATTLER_MASTER_MODE <configuration:TATTLER_MASTER_MODE>` -- whether to divert notifications to a debug address, or to send them to the real recipient.

As the number of variable grows, you'll get unconfortable with a long command-line.

And that becomes critical once you want to pass sensitive data, such as database access credentials, potentially for your own :doc:`plug-ins <plugins>`.

To clean that up, wrap all configuration variables into an `envdir <https://pypi.org/project/envdir/>`:

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

Go through the :doc:`configuration reference <configuration>` for the full list of your options.

Provide access to template designers
------------------------------------

The database of :ref:`Event templates <keyconcepts:event templates>` is a plain folder,
competently assembled by your :ref:`template designer <roles:template designers>`.

As long as you are not in production, both you and them will want to empower them to self-deploy such database:

- So you don't need to do it yourself.
- So they can iterate and test as often as they want without you being in the way.

Do so by simply providing them with filesystem access to the relevant folder, e.g. with rsync.

When you reached production, you might want to restrict this process to avoid issues like accidental removal of all templates.

You may do so by having a "shadow" template folder that template designers have access to, and then a script which runs some basic validation before syncing this folder over to the live folder.

Your validation may include:

- no scope has been removed
- no more than X% of events has been removed
- every event template is well-formed
- every template event sends successfully in debug mode

.. note:: Tattler's :ref:`enterprise distribution <index:enterprise users>` includes scripts for these more advanced scenarios.

Deploy custom plug-ins
----------------------

If custom :doc:`plug-ins <plugins>` are needed, your :ref:`developers <roles:application developers>` will provide you with a folder holding one or more files ending in ``_tattler_plugin.py``.

To enable plug-ins, simply:

1. make this folder accessible to tattler.

2. point tattler to it with configuration variable :ref:`TATTLER_PLUGIN_PATH <configuration:TATTLER_PLUGIN_PATH>`.

Then comes the question of access.

To what systems these plug-ins need access to, and what type of access, is obviously determined by the plug-in itself. Your developers will tell you.

Plug-ins run into tattler's own execution environment, so whatever access they need, tattler needs.

Say -- for example -- you received a folder with 2 tattler plug-ins:

- an :ref:`AddressBook plug-in <plugins:addressbook plug-ins>` which requires access to the users' database
- a :ref:`Context plug-in <plugins:addressbook plug-ins>` which requires lookups into the paying system's REST API

You will need to provide tattler with the following:

- network reachability to the users' database IP and port
- configuration to connect to that database
- network reachability to the paying system's REST API

