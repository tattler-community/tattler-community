Deploy custom plug-ins
======================

If custom :ref:`plug-ins <plugins/index:Tattler plug-ins>` are needed, your :ref:`developers <roles:application developers>` will provide you with a folder holding one or more files ending in ``_tattler_plugin.py``.

To enable plug-ins, simply:

1. make this folder accessible to tattler.

2. point tattler to it with configuration variable :ref:`TATTLER_PLUGIN_PATH <configuration:TATTLER_PLUGIN_PATH>`.

Then comes the question of access.

To what systems these plug-ins need access to, and what type of access, is obviously determined by the plug-in itself. Your developers will tell you.

Plug-ins run into tattler's own execution environment, so whatever access they need, tattler needs.

Say -- for example -- you received a folder with 2 tattler plug-ins:

- an :ref:`AddressBook plug-in <plugins/addressbook:addressbook plug-ins>` which requires access to the users' database
- a :ref:`Context plug-in <plugins/addressbook:addressbook plug-ins>` which requires lookups into the paying system's REST API

You will need to provide tattler with the following:

- network reachability to the users' database IP and port
- configuration to connect to that database
- network reachability to the paying system's REST API

