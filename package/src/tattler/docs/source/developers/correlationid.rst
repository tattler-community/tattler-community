Correlation Ids
---------------

In complex enterprise systems, a transaction often occurs across three or more subsystems.

1. The resource-management system of a supplier might signal that a consultant is no longer available.

2. The company's booking system then invalidates all open appointments for that consultant, and trigger a notification with tattler.

3. tattler sends the notification.

3 separate systems and log files -- a nightmare for the support team when it has to investigate
why a client was notified of a cancellation.

Enter correlation identifiers:

1. The supplier's resource-management system -- the "origin" -- creates a random, unique string called ``correlationId``. It mentions this string into its own logs, and passes it on to the company's booking system.

2. The company's booking system mentions this string as-is in its own log entries about the transaction. It also passes it on again to tattler when triggering the notification.

3. tattler again mentions this string as-is in its own logs about the transaction.

The support team can now simply grep log files from the 3 systems and gain access to the entire
trace of this transaction across all systems.
