Upgrading tattler
=================

Minor versions (e.g. 3.3 to 3.4) are backwards compatible: just upgrade.

Major versions (e.g. 3.x to 4.x) may require changes on your side. For those, follow the section of each major version
you cross, in order.

General procedure
-----------------

1. Read the `CHANGELOG <https://github.com/tattler-community/tattler-community/blob/main/CHANGELOG.md>`_ entries of all versions you cross.

2. Upgrade a staging deployment first:

   .. code-block:: bash

       pip install --upgrade 'tattler==4.*'

3. Restart tattler and check its startup log for warnings and errors.

4. Fire a test notification, e.g. with :ref:`tattler_notify <clitools:tattler_notify>` in ``debug``
   :ref:`notification mode <keyconcepts/mode:notification mode>`.

5. Repeat in production.

Upgrading to 4.x
----------------

1. **Which python version do you run tattler with?**

   Tattler 4 requires python 3.11 or later. If you run an older version, upgrade python first, then
   :ref:`re-create tattler's virtual environment <sysadmins/install_venv:install into a virtual environment>`.

2. **Do you deploy custom plug-ins?** That is, is :ref:`TATTLER_PLUGIN_PATH <configuration:TATTLER_PLUGIN_PATH>` set?

   If not, skip to the next step. If so, check your plug-in folder:

   - Is every plug-in a single file named ``*_tattler_plugin.py``? Tattler 4 ignores plug-ins packaged as folders
     (``foo_tattler_plugin/__init__.py``), and logs a warning for each. Turn them into single files.
   - Do two plug-ins define classes with the same name? Tattler 4 refuses to start. Rename one class.
   - Is any plug-in file named like a built-in one, i.e. ``bulkgate_tattler_plugin.py``, ``bulksms_tattler_plugin.py``
     or ``passthrough_addressbook_tattler_plugin.py``? Tattler 4 refuses to start. Rename the file.

   Then restart tattler and check that its log has one line ``Loading plugin <class name> ...`` for each of your plug-in classes.

3. **Do you deliver SMS notifications?**

   No action needed: :ref:`TATTLER_BULKSMS_TOKEN <configuration:TATTLER_BULKSMS_TOKEN>` works as before.

   Optionally, add `BulkGate <https://www.bulkgate.com>`_ as an alternative or failover gateway with
   :ref:`TATTLER_BULKGATE_TOKEN <configuration:TATTLER_BULKGATE_TOKEN>`.

4. **Does your own python code import tattler server modules?** Other than plug-in interfaces from ``tattler.server.pluginloader``.

   Tattler 4 removes these internals, which handled SMS delivery before it became pluggable:

   - ``tattler.server.sendable.vector_sms``: ``ENVVAR_NAME``, ``get_auth_from_environment()``, ``SMSSendable.get_sms_server()``
   - ``tattler.server.pluginloader.get_plugin_names()``

   To deliver SMS through a custom provider, write an :ref:`SMS backend plug-in <plugins/smsbackend:SMS backend plug-ins>`.
