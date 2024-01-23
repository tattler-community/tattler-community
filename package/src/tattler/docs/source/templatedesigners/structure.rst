Overall template structure
--------------------------

Templates are collected under a single folder, called :ref:`TATTLER_TEMPLATE_BASE <configuration:TATTLER_TEMPLATE_BASE>`.

Get used to where it is, because you'll spend the bulk of your time inside it over the next few weeks 😉

Scopes
^^^^^^

The :ref:`TATTLER_TEMPLATE_BASE <configuration:TATTLER_TEMPLATE_BASE>` folder contains one sub-folder for each
:ref:`scope <keyconcepts/scopes:notification scopes>`.

And each scope-folder contains events for that scope.
If scopes confuse you, define them later, together with your :ref:`developer <developers/index:developers>`.

You can start by wrapping all events into one single scope -- say "myWebApp" -- so your
``TATTLER_TEMPLATE_BASE`` folder structure would look like this:

.. code-block:: text
    
    templates_base/
    ├── mywebapp/                       <-- a scope
    └── my_booking_sys/                 <-- another scope

Events
^^^^^^

Events are folders within a scope. So once you create folders -- under your scope "myWebApp" --
for the events your fantasy :ref:`product manager <productmanagers:the table>`, your ``TATTLER_TEMPLATE_BASE``
would look like this:

.. code-block:: text

    templates_base/
    └── mywebapp/                       <-- a scope
        ├── reservation_confirmed/      <- an event
        └── password_changed/           <- another event

Vectors
^^^^^^^

Each event may require being sent over email and SMS.

Your :ref:`product manager <productmanagers:the table>` told you which event needs to be sent
with which vector:

- ``reservation_confirmed``: email only.
- ``password_changed``: email and SMS.

We'll now proceed to build those.
