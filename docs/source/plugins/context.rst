Context plug-ins
================

Context plug-ins extend or override :ref:`context variables <keyconcepts/events:Context>` passed to templates.

You may have an arbitrary number of context plug-ins, e.g. to load information about billing,
account status, support tickets etc.

Each context plug-in can indicate whether it should be loaded based on the content of the current context.
This enables them to "fire" based on the event being notified, or the recipient, or more.

.. note:: The class for context plugins was renamed in Tattler version 1.2.0 .

    Up until Tattler version 1.1.1 you would inherit from class
    ``ContextTattlerPlugin`` in order to define a context plug-in.

    Since Tattler version 1.2.0, the class was renamed to
    :class:`ContextPlugin <tattler.server.pluginloader.ContextPlugin>`
    for simplicity and symmetry with
    :ref:`Addressbook plug-ins <plugins/addressbook:Addressbook plug-ins>`.

    Name ``ContextTattlerPlugin`` is still available as an alias for
    backward compatibility, but you'll get a deprecation notice when
    plug-ins inheriting from it are loaded.


Writing a context plug-in
-------------------------

Context plug-ins are python files that

- are placed in the :ref:`plug-in directory <configuration:TATTLER_PLUGIN_PATH>`,
- implement the ``ContextPlugin`` interface of class :class:`tattler.server.pluginloader.ContextPlugin`.

Plug-in filenames **must** end with ``_tattler_plugin.py``; other filenames are ignored.

To create a context plug-in:

1. Familiarize yourself using the :ref:`quickstart example <quickstart:Write a context plug-in>`.

2. Start coding your own starting with the `sample plug-ins <https://github.com/tattler-community/tattler-community/blob/main/plugins/>`_ in Tattler's repository.

See :ref:`Deploying plug-ins <sysadmins/deploy_plugins:Deploy custom plug-ins>` for tips on deployment.
