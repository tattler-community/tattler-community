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


Example plugin
--------------

.. code-block:: python

    # filename: billinginfo_tattler_plugin.py

    from tattler.server.pluginloader import ContextPlugin

    class BillingInfoTattlerPlugin(ContextPlugin):
        def setup(self):
            self.billingdb = connect(billing_db)

        def processing_required(self, context):
            return 'invoice_number' in context

        def process(self, context):
            return context | {
                'invoice_date': self.billingdb.select(number=context['invoice_number']).date,
                'invoice_amount': self.billingdb.select(number=context['invoice_number']).total_amount,
            }
