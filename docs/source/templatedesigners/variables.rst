Template variables
==================

Variables can come into templates from 3 places:

1. **tattler variables** -- available in every notification.
2. **client variables** -- available based on what and when the application sends it. Usually one event always receives the same set of variables.
3. **plug-in variables** -- may be a mixture of the two above.

This origin plays no role in the template itself, but you need to know the origin
to know when you can use a variable.

This section lists **tattler variables**. For client variables and plug-in variables,
speak with your :ref:`application developer <roles:application developers>`.


user_id
-------

Type: str

Recipient id as passed to tattler in the client request.


user_email
----------

Type: str | None

E-mail address of the user being notified.


user_sms
--------

Type: str | None

Mobile number of the user being notified.


user_firstname
--------------

Type: str

First name, guessed from the recipient's email address.

The guessing is surprisingly reliable:

- Many users actually use their full name, like ``john.doe@company.com`` or ``thomas.mueller@gmail.com``.
- Heuristics are in place to avoid indeterminate traps like ``info@``. String ``user`` is provided in this case.
- Users like ``jdoe@`` can still make sense of their greeting and understand they are themselves to blame.


This logic may still be overridden by an address book plug-in to produce a reliable first name.
Speak to your :ref:`application developer <roles:application developers>`.

Whether guessed or provided, the first name is 'prettified' as follows:

- If provided as all-lower or all-uppercase, then it's capitalized. E.g. 'michael j' becomes 'Michael J'.
- If provided as mixed case, then it's left as is, under the assumption that the person already took care of casing it correctly. E.g. 'Maria de la Paz' stays such.


user_account_type
-----------------

type: str | None

The name of the account type this user is on. This is always ``None`` unless provided by an address book plug-in.
Speak to your :ref:`application developer <roles:application developers>`.

This is useful e.g. to build conditional text and address paying and free users in different ways.


correlation_id
--------------

Type: str

A cross-system ID for the transaction which eventually triggered this notification.

This string can be searched into log files of all systems involved in the notification request
to troubleshoot what happened.
For example an inventory system triggered the central web application which triggered tattler.

A user may spell out this string for the support team to perform root-cause analysis of unexpected
events.

This string may be considered internal information, so think twice before exposing it.
Variable `notification_id`_ is usually a better choice.


notification_id
---------------

Type: str

A unique identifier for the notification.

A user may spell out this string for the support team to identify what notification they are referring to.

This notification_id will also be logged into tattler log files, so it can be used to get to the
`correlation_id`_, which can be then used for root-cause analysis.

This provides a clear separation of user-facing information vs internal information.


notification_mode
-----------------

Type: str

Which :ref:`notification mode <keyconcepts/mode:notification mode>` the notification was sent with.


notification_vector
-------------------

Type: str

Name of the vector which is being sent. The template designer usually knows already, but this may be useful
in some advanced template scenarios.


notification_scope
------------------

Type: str

Name of the scope of the event.


event_name
----------

Type: str

Name of the event itself.
