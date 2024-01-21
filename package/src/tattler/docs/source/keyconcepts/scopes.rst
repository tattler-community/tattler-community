
Notification scopes
-------------------

Real-world IT systems are usually composed of multiple components, and each may need to notify users.

For example:

* A web application sends confirmations about created subscriptions.
* A fulfillment system sends shipment confirmations.
* A payment integration backend sends error notifications when a credit card charge failed.

Each such system has its own sets of events to notify, and this set should not be mixed with other applications.

This is what tattler calls a "scope".

A scope is a collection of events under one name, which is usually the name of the system requesting them.

Scopes affect you as a user in 2 ways:

* You need to split your templates by scope.
* You need to indicate the scope for each event you request notification for.

Scopes are **mandatory**: even if you only use tattler from one application, you need to arrange your
notification templates under one scope, and you need to indicate that scope when you issue notification
requests to tattler.


Organizing event templates by scope
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Scopes are non-empty text strings which may only contain letters, numbers and the `_` symbol.
For example ``billing_system2_partners``.

Notification scopes are visible in tattler's :ref:`configuration:TATTLER_TEMPLATE_BASE`: they are
the first-level children (mywebapp, fulfiller, pmtintegrator).

.. code-block:: text
    
    templates_base/
    ├── mywebapp/               <-- a scope
    │   ├── password_changed/    <- an event
    │   └── order_accepted/
    ├── fulfiller/              <-- a scope
    │   ├── order_shipped/       <- an event
    │   ├── delay_occurred/
    │   └── shipping_error/
    └── pmtintegrator/          <-- a scope
        └── cc_charge_failed/    <- an event


Indicating the scope in requests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pass the scope in the URL of your notification requests:

.. code-block:: bash

    #             |-------- server endpoint ---------| |-scope-| |----event----|
    curl -X POST 'https://127.0.0.1:11503/notification/mywebapp/password_changed/?user=your@email.com'
