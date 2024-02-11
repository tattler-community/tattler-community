.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

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

.. toctree::

    types
    addressbook
    context
    addressbookplugin_reference
    contextplugin_reference