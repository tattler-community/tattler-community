What systems trigger notifications (scope)
------------------------------------------

Start from the :ref:`events list <productmanagers:the table>` from your
product manager.

Understand what events must be notified, and what systems
in your overall system should trigger those.

Map each notification to its triggering system:

+-----------------------+-------------------+
| Event                 | Triggering system |
+=======================+===================+
| Reservation confirmed | myWebApp          |
+-----------------------+-------------------+
| Password changed      | myWebApp          |
+-----------------------+-------------------+
| Appointment reminder  | myBookingSys      |
+-----------------------+-------------------+
| CredCard charge error | pmtintegrator     |
+-----------------------+-------------------+

Each system that triggers a notification will identify itself as
a :ref:`scope <keyconcepts/scopes:notification scopes>` to tattler.

Communicate the scopes to your :ref:`template designer <roles:template designers>`
so they can start organizing the templates for each event.

