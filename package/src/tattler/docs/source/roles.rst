.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

Roles
=====

Here are the roles across tattler's value chain:

.. mermaid::

    flowchart LR

    PM[Product\nManager] --> TD[Template\ndesigner] --> DEV[Application\nDeveloper] --> SysAdm[System\nAdministrator] --> User[Application\nUser]


And their responsibility:

+-----------------------+-------------------------------------------------------+----------------------------------------------------+
| Role                  | Responsibility                                        | Deliverables                                       |
+=======================+=======================================================+====================================================+
| Product Manager       | Define events upon which notifications are sent.      | List of events.                                    |
+-----------------------+-------------------------------------------------------+----------------------------------------------------+
| Template designer     | Write & style notification content.                   | Notification templates for every event and vector. |
+-----------------------+-------------------------------------------------------+----------------------------------------------------+
| Application developer | Build code to trigger notification for each event.    | Client code.                                       |
+-----------------------+-------------------------------------------------------+----------------------------------------------------+
| System administrator  | Deploy, configure, secure, maintain tattler.          | Ever running tattler.                              |
+-----------------------+-------------------------------------------------------+----------------------------------------------------+
| Application user      | Provide contacts for each vector. Enjoy notifications.| Own contacts for each vector.                      |
+-----------------------+-------------------------------------------------------+----------------------------------------------------+


Product managers
----------------

They define what notifications are sent upon which business event.

They also define:

- what :ref:`vectors <keyconcepts/vectors:notification vectors>` the event should be notified in (email? SMS? telegram?).
- what general information should be sent to the user upon that event.

Deliverables:

- A table listing events (rows) and what vectors they should be notified to (columns).

See documentation for :doc:`product managers <productmanagers>`.

Template designers
------------------

They write and style the concrete notification templates for every event and vector.
This is the largest bulk of the work in the chain.

As part of this, they need to:

- Know or define what variables to use in their templates.
- name the templates and communicate those names to developers.

See documentation for :ref:`template designers <templatedesigners/index:template designers>`.

Application developers
----------------------

They determine which systems will trigger notifications for which events (i.e. what :ref:`scopes <keyconcepts/scopes:notification scopes>` are available).

They then code the code to ask tattler to actually send those events.

In some advanced scenarios, they also write plug-ins for tattler, for example:

- "Addressbook" plug-ins: to extract contact information about users, so enterprise applications only tell tattler to "notify user #123 about event 'password_changed'", and tattler is able to look up the respective email address and mobile number.
- "Context" plug-ins: to provide variables to template designers. For example, variables hosting the plan the user is on, or how much of the purchased resources is currently used.

See documentation for :ref:`developers <developers/index:developers>`.

Application users
-----------------

Tattler is completely invisible to the receiving user.

The user simply receives notifications, lovingly crafted by the template designer.

System administrators
---------------------

They make sure that tattler gets to run and then stays running.

They are resposible for:

- Installation and configuration of tattler.
- Optionally containarization.
- Configuration of system and network so every relevant 3rd system can reach Tattler's notification interface.
- Software updates.

See documentation for :doc:`system administrators <sysadmins/index>`.
