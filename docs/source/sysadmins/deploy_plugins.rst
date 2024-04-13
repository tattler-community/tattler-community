Deploy custom plug-ins
======================

If custom :ref:`plug-ins <plugins/index:Tattler plug-ins>` are needed, your :ref:`developers <roles:application developers>` will provide you with a folder holding one or more files ending in ``_tattler_plugin.py``.

To enable plug-ins, simply:

1. make this folder accessible to tattler.

2. point tattler to it with configuration variable :ref:`TATTLER_PLUGIN_PATH <configuration:TATTLER_PLUGIN_PATH>`.

Plug-in deployment folder
-------------------------

Where to place the plug-in folder?

Consider two locations:

- a ``/usr/libexec/tattler`` directory, if you installed tattler into your main filesystem hierarchy. This is the option recommended to package builders.
- a ``tattler/plugins`` directory, if you installed tattler into a standalone directory.

Providing access
----------------

Then comes the question of access:

- To what systems these plug-ins need access to? Database? Filesystem?
- What type of access? Read? Read-Write? Delete?

This is obviously plug-in dependent -- so discuss with your developers.

Plug-ins run into tattler's own execution environment, so whatever access they need, tattler needs.

Say -- for example -- you received a folder with 2 tattler plug-ins:

- an :ref:`AddressBook plug-in <plugins/addressbook:addressbook plug-ins>` which requires access to the users' database
- a :ref:`Context plug-in <plugins/addressbook:addressbook plug-ins>` which requires lookups into the paying system's REST API

You will need to provide tattler with the following:

- network reachability to the users' database IP and port
- configuration to connect to that database
- network reachability to the paying system's REST API

