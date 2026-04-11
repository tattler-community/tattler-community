Documenting templates
=====================

As you build templates, do document them by providing a ``context.json`` file alongside each event.

This file lists the variables your template expects, with a sample value for each:

.. code-block::

    templates/
    └── mywebapp/                    # scope
        └── order_confirmation/      # event
            ├── context.json         # <-- document your template here
            └── email/
                ├── body.html
                ├── body.txt
                └── subject.txt

With content like:

.. code-block:: JSON

    // sent to the customer when an order is confirmed
    {
        "order": {
            "number": "ORD-1234",
            
            // always with 2 decimals, incl 0.00
            "total": 49.90,
            
            // always in the past
            "placed_at": "^tattler^datetime^2024-06-28T18:15:04"
            
            "reseller": "partner12" // null if sold directly
        },
        // name as registered in the user's profile, including middle name if any
        "customer_name": "Jane M. Doe"
    }

The actual values are irrelevant -- only keys and types matter. For example,
``"number": "ORD-1234"`` declares that ``order.number`` is a string, and
``"total": 49.90`` declares it is a float.

Use ``//`` comments to describe the meaning of fields that aren't self-evident.

.. tip::

    For temporal types, use :ref:`tattler's type markers <testing/livepreview:Parameter encoding>`
    (e.g. ``^tattler^datetime^...``) so the declaration carries the correct Python type.


Comment generously
------------------

Use comments in your ``context.json`` file e.g. to:

- Describe what the notification is, upon what event it's fired, and to whom
- What fields mean
- When types can be ``null``
- Any constraints on values


Why bother?
-----------

Track the data you need
^^^^^^^^^^^^^^^^^^^^^^^

``context.json`` tracks all variables required by your templates in a single place, including their types and meaning.

Tracking that by going through templates quickly gets out of hand with multiple template files for email parts, SMS etc.


Interface to developers
^^^^^^^^^^^^^^^^^^^^^^^

Your application developers need to know exactly what data to pass when triggering a
notification.

``context.json`` gives them a clear, concrete contract to fulfill:

- Which keys are expected.
- What type each value should have (string, number, datetime, nested object, ...).
- What the structure of complex objects looks like.

This replaces ad-hoc communication ("which fields does ``order_confirmation`` need again?")
with a self-service reference that stays in sync with the template.


Enable automations
^^^^^^^^^^^^^^^^^^

``context.json`` enables automated testing to automatically verify that
their code supplies all data you need.

If they or you alter anything, those tests will immediately report:

- A new key that you require and they fail to provide
- An item that they provide with the wrong value (e.g. int instead of string)
- A wrong structure, e.g. a misplaced key, or a string instead of a list.

See :ref:`developers/testing_notifications:Testing notifications` .

Additionally, ``context.json`` files are used to fill out sample data in live previews.
See :ref:`testing/livepreview:Live previews`.