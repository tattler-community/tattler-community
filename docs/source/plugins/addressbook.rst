Addressbook plug-ins
====================

Address book plug-ins look up user information:

- email address
- mobile number
- first name
- account type
- user's language preference (if you use :ref:`multilingual notifications <templatedesigners/multilingualism:Multilingual notifications>`)

They allow client applications to tell tattler "Notify user #123 about event XYZ", and
tattler takes care of loading the necessary contacts depending on what
:ref:`vectors <keyconcepts/vectors:notification vectors>` the event should be sent to.

You may provide multiple address book plug-ins. They are processed in sequence until
one is able to return contacts for the user inquired.

Writing an address book plug-in
-------------------------------

Address book plug-ins are python files that

- are placed in the :ref:`plug-in directory <configuration:TATTLER_PLUGIN_PATH>`,
- implement the ``AddressbookPlugin`` interface of class :class:`tattler.server.pluginloader.AddressbookPlugin` .

Plug-in filenames **must** end with ``_tattler_plugin.py``; other filenames are ignored.

To create an addressbook plug-in:

1. Familiarize yourself using the :ref:`quickstart example <quickstart:Write an addressbook plug-in>`.

2. Start coding your own starting with the `sample plug-ins <https://github.com/tattler-community/tattler-community/blob/main/plugins/>`_ in Tattler's repository.

See :ref:`Deploying plug-ins <sysadmins/deploy_plugins:Deploy custom plug-ins>` for tips on deployment.


More details
------------

- :ref:`Requirements on tattler plug-ins <plugins/types:Plug-in interface>` in general.
- :ref:`Provisioning multiple plug-ins <plugins/types:Plug-in chains>`.
- :ref:`AddressbookPlugin class reference <plugins/addressbookplugin_reference:AddressbookPlugin reference>`.