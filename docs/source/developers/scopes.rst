Client applications
-------------------

A tattler client is an application that uses tattler to deliver notifications, i.e. usually **your application**.

To let your application fire notifications via tattler you have 2 options:

- If your application is written in python, use tattler's client library.

- If your application is written in any other language, hit tattler's REST API.

Scopes
++++++

You usually want to give every application a :ref:`scope <keyconcepts/scopes:Notification scopes>` in tattler.

This allows you to isolate the notifications fired by this application, which helps you keep
your notifications clear and organized -- and simplifies the context to keep in mind for
template designers.

How to define scopes
++++++++++++++++++++

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

