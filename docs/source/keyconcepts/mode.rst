
Notification mode
-----------------

Notification mode simplifies development and operations.

It allows client applications to send "real" notification requests -- e.g. with actual client addresses --
while only sending to an `internal address <supervisor recipient>`_ used to verify the output.

Regardless of the mode, notification content is always composed exactly as it would in a "live" environment
(e.g. the "To:" address of emails will include the actual recipient), but the actual notification is
only delivered to an `debug recipient`_ (``debug``) or copied to a
`supervisor recipient`_ (``staging``).

Available modes
^^^^^^^^^^^^^^^

The *mode* is applicable to every notification request, and can be controlled:

- per-request with the ``mode=`` parameter
- at the global level with the :ref:`TATTLER_MASTER_MODE <configuration:TATTLER_MASTER_MODE>` option.

There are 3 modes:

``production``
    Send notification to actual recipient.

``staging``
    Send notification to actual recipient, and also send a copy to debug recipient.
    This is helpful for support teams to keep track of all notifications delivered.

``debug``
    Do not send anything to the actual recipient. Instead, send exclusively to the debug recipient.
    This is useful for developers to safely test their logic operating on real data without
    bothering users nor adapting their code in all systems to avoid doing so.

The default mode is ``debug``, because "better safe than sorry".

Master vs per-request mode
^^^^^^^^^^^^^^^^^^^^^^^^^^

The *master mode* "limits" any per-request mode as a highest possible mode.

That means, a client can request a lower or equal mode than the master, but not a higher one.

.. _supervisor_recipient:

Supervisor recipient
^^^^^^^^^^^^^^^^^^^^

Configured with the :ref:`configuration:TATTLER_SUPERVISOR_RECIPIENT_*` envvar.

All notifications are copied to this address, when they are sent in ``staging`` `notification mode`_.

* The recipient indicated in the request receives the notification.
* The "supervisor recipient" receives a copy of every notification, regardless of the requested recipient.
* The notification content reflects the requested recipient (e.g. the "To:" field of emails, or any reference in the body).
* Log files mention both the requested and the delivered recipients.


Debug recipient
^^^^^^^^^^^^^^^

Configured with the :ref:`configuration:TATTLER_DEBUG_RECIPIENT_*` envvar.

All notifications are sent exclusively to this address, when they are sent in ``debug`` `notification mode`_.

* The recipient indicated in the request receives nothing.
* The "debug recipient" receives every notification requested, regardless of the requested recipient.
* The notification content reflects the requested recipient (e.g. the "To:" field of emails, or any reference in the body).
* Log files mention both the requested and the delivered recipients.
