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

Keep in mind that plug-in filenames **must** end with ``_tattler_plugin.py``; other filenames are ignored.

To create an addressbook plug-in, refer to the
:ref:`respective section in the quickstart <quickstart:Write an addressbook plug-in>`.

Tattler's repository includes
`sample plug-ins <https://github.com/tattler-community/tattler-community/blob/main/plugins/sqladdressbook_tattler_plugin.py>`,
so it's a good idea for you to start from there.

You may organize tattler plug-ins in either of two locations:

- a ``/usr/libexec/tattler`` directory, if you opted to place tattler data into your main filesystem hierarchy.
- a ``tattler/plugins`` directory, if you opted to place tattler data into an own directory.

More details
------------

- :ref:`Requirements on tattler plug-ins <plugins/types:Plug-in interface>` in general.
- :ref:`Provisioning multiple plug-ins <plugins/types:Plug-in chains>`.
- :ref:`AddressbookPlugin class reference <plugins/addressbookplugin_reference:AddressbookPlugin reference>`.