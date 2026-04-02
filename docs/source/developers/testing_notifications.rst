Testing notifications
---------------------

When your application calls ``send_notification()`` with a context dict, the template
expects certain keys to be present with certain types. A mismatch -- a missing key or
a wrong type -- only surfaces at notification time, possibly in production.

Tattler lets you declare the expected context for each event in a ``context.json`` file
and validate your code against it in your test suite. This same `context.json` is also
used for :ref:`live previews <testing/livepreview:Live previews>`.


Declaring the expected context
++++++++++++++++++++++++++++++

Place a ``context.json`` file inside the event template directory:

.. code-block::

    templates/
    └── mywebapp/                    # scope
        └── order_confirmation/      # event
            ├── context.json         # expected context declaration
            └── email/
                ├── body.txt
                └── subject.txt

The file contains a JSON object whose keys and value types mirror what your
template expects:

.. code-block:: JSON

    {
        "order": {
            "number": "ORD-1234",
            "total": 49.90,
            "placed_at": "^tattler^datetime^2024-06-28T18:15:04"
        },
        "customer_name": "Jane Doe"
    }

The actual values are irrelevant -- only keys and types matter. For example,
``"number": "ORD-1234"`` declares that ``order.number`` must be a string, and
``"total": 49.90`` declares it must be a float.

For temporal types, use :ref:`tattler's type markers <testing/livepreview:Parameter encoding>`
(e.g. ``^tattler^datetime^...``) so the declaration carries the correct Python type.

A ``null`` value means "any type is accepted" -- useful for optional or polymorphic fields.


Validating context in tests
+++++++++++++++++++++++++++

Tattler provides :func:`~tattler.utils.context_validation.assert_context_complete`,
a helper designed for use in ``unittest`` test cases. It checks that a context dict:

1. Is serializable (can survive the client-to-server wire format).
2. Contains all keys declared in ``context.json``.
3. Has values whose types match those declared.

Say your application has a function that builds a context and sends a notification:

.. code-block:: python

    # myapp/notifications.py
    from datetime import datetime
    from tattler.client.tattler_py import send_notification

    def notify_order_confirmed(customer, order):
        """Send an order-confirmation notification."""
        ...
        context = {
            'order': order,         # send_notification() serializes these objects into JSON
            'customer': customer,
        }
        send_notification('mywebapp', 'order_confirmation', customer.email, context=context)

To validate the context, mock ``send_notification()`` and pass the captured context
to ``assert_context_complete()``:

.. code-block:: python

    # tests/test_notifications.py
    import unittest
    from pathlib import Path
    from unittest import mock

    from tattler.utils.context_validation import assert_context_complete

    from myapp.notifications import notify_order_confirmed

    TEMPLATES_ROOT = Path('/path/to/templates')

    class TestOrderNotifications(unittest.TestCase):

        def test_order_confirmation_context(self, mock_send):
            """Verify the context we pass matches what the template expects."""

            with mock.patch('myapp.notifications.send_notification') as mock_send:
                # have the code call send_notification()
                notify_order_confirmed(order, customer)
                # validate the context it provided to send_notification()
                _, kwargs = mock_send.call_args
                context = kwargs['context']
                assert_context_complete(self, 'mywebapp', 'order_confirmation', context, TEMPLATES_ROOT)

If the context is missing a key, has a wrong type, or is not serializable, the test
fails with a clear message listing every violation:

.. code-block::

    mywebapp/order_confirmation: context validation failed:
      '.order.placed_at': expected datetime, got str
      '.customer_name': missing key


What gets checked
+++++++++++++++++

- **Missing keys** -- every key in ``context.json`` must be present in the actual context.
- **Type mismatches** -- the Python type of each value must match (``int``, ``str``, ``float``, ``datetime``, etc.).
- **Nested dicts** -- validated recursively, with dotted paths in error messages (e.g. ``order.total``).
- **Lists of dicts** -- each element is validated against the first element declared in ``context.json``.
- **Lists of scalars** -- only the list type itself is checked, not individual element types.
- **Serializability** -- ORM objects, model instances and other non-JSON types are serialized first, and the test fails if serialization itself fails.
- **Extra keys** -- keys present in the actual context but absent from ``context.json`` are accepted silently.
- **Null declarations** -- a ``null`` value in ``context.json`` accepts any type in the actual context.
- **Null values in context** -- by default, ``None`` values in the actual context are accepted even when ``context.json`` declares a non-null type. Pass ``accept_null=False`` to reject them.


Typical workflow
++++++++++++++++

1. Your :ref:`template designer <roles:template designers>` creates or updates a template and its ``context.json``.

2. You write a test that builds the context your code will pass to ``send_notification()`` and calls ``assert_context_complete()``.

3. When the template interface changes (keys added, types modified), the test fails, telling you exactly what to update in your code.

This keeps your notification-triggering code and your templates in sync, catching
contract violations at test time rather than in production.


API reference
+++++++++++++

.. autofunction:: tattler.utils.context_validation.assert_context_complete
