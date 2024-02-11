.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

Developers
==========

Your role:

- Determine what systems need to trigger notifications for the :ref:`defined events <productmanagers:the table>`.
- Implement logic to call tattler upon each of those events.

Potential follow-up tasks:

- Decide if user contacts should be looked up by every system of yours, or rather tattler. In the latter case, you'll want to write an :ref:`addressbook plug-in <plugins/addressbook:addressbook plug-ins>`.
- Decide with your :ref:`template designer <roles:template designers>` if several templates need some additional variables that you do not want to load in every system. In which case, you'll want to write a :ref:`context plug-in <plugins/context:context plug-ins>`.


.. toctree::

    scopes
    trigger
    api_http
    api_python_high
    api_python_low
    correlationid


