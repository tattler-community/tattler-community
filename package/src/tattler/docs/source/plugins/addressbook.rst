Addressbook plug-ins
====================

Addressbook plug-ins look up user information:

- email address
- mobile number
- first name
- account type
- user's language preference (if you use :ref:`multilingual notifications <templatedesigners/multilingualism:Multilingual notifications>`)

They allow client applications to tell tattler "Notify user #123 about event XYZ", and
tattler takes care of loading the necessary contacts depending on what
:ref:`vectors <keyconcepts/vectors:notification vectors>` the event should be sent to.

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
        TATTLER_TEMPLATE_BASE=~/notification_events \
        TATTLER_MASTER_MODE=production \
        tattler_server

Tattler will log the following while starting::

    [..] Loading plugin CompanyAddressbook (<class 'mycontacts_tattler_plugin.CompanyAddressbook'>) from module mycontacts_tattler_plugin

More details
------------

- :ref:`Requirements on tattler plug-ins <plugins/types:Plug-in interface>` in general.
- :ref:`Provisioning multiple plug-ins <plugins/types:Plug-in chains>`.
- :ref:`AddressbookPlugin class reference <plugins/addressbookplugin_reference:AddressbookPlugin reference>`.