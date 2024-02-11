Notification events
-------------------

Your applications use tattler to deliver notifications upon certain events,
for example "password changed", "order accepted", "payment failed" etc.

tattler knows itself what actual content to send for the requested event,
because you provide `event templates`_ to it.

You provide event templates as part of tattler configuration.

They are usually written by :ref:`template designers <templatedesigners/index:template designers>`.


Event templates
^^^^^^^^^^^^^^^

Event templates are text which gets expanded to generate an actual notification to send about an event.

tattler uses Jinja as default template processor, so an event template for SMS could look like this::

    Hi {{ user_firstname }}. Be advised that your account password got changed today at {{ appointment_time }}. The address is {{ update_time }}.

Some properties of event templates:

* Are vector-specific, i.e. you'll have different content to deliver the same event via email vs SMS.
* Can be parameterized with variables -- which is why they are "templates". See `Context`_
* Can contain multiple parts. For example, emails include a subject, a body, and potentially HTML content.
* Are "expanded" at delivery time, so you can change them without restarting ``tattler_server``.
* Are stored as files in a directory structure.

Context
^^^^^^^

A context is a set of variables used to expand a template.

Variables available to a template come from various sources:

- tattler provides some :ref:`core variables <templatedesigners/variables:template variables>` itself.
- :ref:`context plug-ins <plugins/context:context plug-ins>` may add custom variables.
- the client requesting notification may add further variables.

