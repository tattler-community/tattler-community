Tattler plug-ins
==================

Tattler really shines when you start moving notification logic away from your triggering
applications and into tattler itself, so it can be re-used by all systems that trigger notifications.

You do this with plug-ins.

Plug-ins allow you to:

- Look up user information -- like email, mobile number, first name etc -- so your applications can simply ask "Notify user #123 about event XYZ".
- Build context information -- like data about their open orders, pending payments, usage history etc.

The idea is to build these look-ups once into tattler, so you don't have to bloat
application code with notification logic, potentially multiple times.


Addressbook plug-ins
--------------------

Addressbook plug-ins look up user information:

- email address
- mobile number
- first name
- account type

They allow client applications to tell tattler "Notify user #123 about event XYZ", and
tattler takes care of loading the necessary contacts depending on what
:ref:`vectors <keyconcepts:notification vectors>` the event should be sent to.

You may provide multiple addressbook plug-ins. They are processed in sequence until
one is able to return contacts for the user inquired.

Writing an addressbook plug-in
------------------------------

Addressbook plug-ins are python files that

- are placed in the :ref:`plug-in directory <configuration:TATTLER_PLUGIN_PATH>`,
- implement the AddressbookPlugin interface.

Create a directory for plug-ins:

.. code-block:: bash

    # create a directory to hold tattler plug-ins
    mkdir -p ~/tattler_plugins
    # create a file for your AddressBook plug-in (mind the suffix!)
    touch ~/tattler_plugins/mycontacts_tattler_plugin.py

Plug-in filenames **must** end with ``_tattler_plugin.py``; other filenames are ignored.

Now implement the addressbook plug-in:

.. code-block:: python

    # file ~tattler_plugins/mycontacts_tattler_plugin.py
    """AddressBook plug-in for tattler to load contacts from the enterprise' IAM"""

    import urllib.request

    from tattler.server.pluginloader import AddressbookPlugin

    # load contact data from a CSV filename, formatted like this:
    #   user_id,email,mobile_number
    email_csv_filename = '/var/db/user_emails.csv'

    class CompanyAddressbook(AddressbookPlugin):
        def email(self, recipient_id, role=None):
            """Look up email address in email CSV file"""
            with open(contacts_csv_filename) as csvf:
                for line in csvf:
                    user_id, email, mobile = line.strip().split(',')
                    if user_id == recipient_id:
                        return email
            return None

        def mobile(self, recipient_id, role=None):
            """Look up mobile number on intranet webpage"""
            url = f"http://company.intranet/contacts/{recipient_id}/mobile/"
            try:
                with urllib.request.urlopen(url) as resp:
                    return resp.read(300)
            except:
                pass
            return None

Done.

Now reload tattler with the new plug-in directory:

.. code-block:: bash

    TATTLER_PLUGIN_PATH=~/tattler_plugins \
        TEMPLATE_BASE=~/notification_events \
        MASTER_MODE=production \
        tattler_server

Tattler will log the following while starting::

    [..] Loading plugin CompanyAddressbook (<class 'mycontacts_tattler_plugin.CompanyAddressbook'>) from module mycontacts_tattler_plugin


AddressbookPlugin interface
---------------------------

You may provide an arbitrary number of addressbook plug-ins within the configured
:ref:`plugin folder <configuration:TATTLER_PLUGIN_PATH>`.

Tattler loads plug-ins once, at startup. Restart Tattler server to add, remove or alter plug-ins.

Tattler only loads plug-ins that fulfill the following:

- Be written in python.
- Be placed in the ``TATTLER_PLUGIN_PATH`` folder.
- Be filenamed with suffix ``_tattler_plugin.py``.
- Contain one class which subclasses ``tattler.server.pluginloader.AddressbookPlugin``.

If tattler finds multiple addressbook plug-ins, it:

1. Loads them all at startup.

2. Queries them sequentially by alphanumerical order of the plug-in's class name (not file name!).

3. Terminates the look up at the first addressbook plug-in returning data.


The complete AddressbookPlugin interface looks like this:

.. autoclass:: tattler.server.pluginloader.AddressbookPlugin
    :members: recipient_exists, email, mobile, account_type, first_name, attributes


Context plug-ins
----------------

Context plug-ins extend or override :ref:`context variables <keyconcepts:Context>` passed to templates.

You may have an arbitrary number of context plug-ins, e.g. to load information about billing,
account status, support tickets etc.

Each context plug-in can indicate whether it should be loaded based on the content of the current context.
This enables them to "fire" based on the event being notified, or the recipient, or more.

Provisioning plug-ins
---------------------

Both Addressbook and Context plug-ins are processed in a chain: the first plug-in receives the "native" context as generated
by Tattler, and returns a new context which is then fed into the second plugin, and so on.

.. mermaid::

    flowchart LR
        TattlerServer --> |native context| Plugin1
        Plugin1 --> |context1| Plugin2
        Plugin2 --> |context2| Templates


Plugin provisioning
-------------------

Plugins are python files complying with a certain interface, and placed in a directory which is pointed to with the ``TATTLER_PLUGIN_PATH`` envvar.
Plugins are loaded once,xw at startup. To add plugins, restart Tattler server.

Within the configured plugin folder, Tattler checks plugins for compatibility with the [Plugin interface](#plugin-interface)::

    my_plugin_path/
    ├─ foo.py                       # <- will be ignored: wrong suffix
    ├─ users_tattler_plugin.py
    └─ billing_tattler_plugin.py

Plugin interface
----------------

Requirements for every plugin:

- Be written in python
- Be placed in the ``TATTLER_PLUGIN_PATH`` folder
- Be filenamed with suffix ``_tattler_plugin.py``
- Contain one class which subclasses ``tattler.server.pluginloader.ContextTattlerPlugin``

This class has 3 key methods:

.. code-block:: python

    from typing import Mapping, Any

    ContextType = Mapping[str, Any]

    class ContextTattlerPlugin:
        """Base class that every context plugin inherits from."""

        def setup(self) -> None:
            """Perform a one-off initialization of this plugin, e.g. connect to DB.

            Overriding this method is optional. If a plugin's setup() method raises an exception,
            the plugin is not activated.
            """
            pass

        def processing_required(self, context: ContextType) -> bool:
            """Returns whether this plugin should be called, based on the context."""
            return True

        def process(self, context: ContextType) -> ContextType:
            """Actually run the plugin, and return a new, potentially modified context."""
            return context

Example plugin
--------------

.. code-block:: python

    # filename: billinginfo_tattler_plugin.py

    from tattler.server.pluginloader import ContextTattlerPlugin

    class BillingInfoTattlerPlugin(ContextTattlerPlugin):
        def setup(self):
            self.billingdb = connect(billing_db)

        def processing_required(self, context):
            return 'invoice_number' in context

        def process(self, context):
            return context | {
                'invoice_date': self.billingdb.select(number=context['invoice_number']).date,
                'invoice_amount': self.billingdb.select(number=context['invoice_number']).total_amount,
            }

