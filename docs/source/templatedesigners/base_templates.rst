Base templates
==============

You usually want to send notifications with a consistent style. Especially for HTML,
where you want to have a common design -- colors, fonts, footer links etc.

Sometimes also for plain-text, where you might want to include disclaimer footers.

The tools you learned so far enable you to do that, but you'd repeat those common
elements in every single event template.

Tattler supports **base templates** to simplify that::

    templates_base/
    ├── _base                           <- base template (NB: _base )
    │   └── email/                      <- base template for email
    │       ├── subject.txt
    │       ├── body.txt
    │       ├── body.html
    │       └── priority.txt
    └── mywebapp/                       <-- a scope
        └── reservation_confirmed/      <- event template
            └── email/
                ├── subject.txt             
                ├── body.txt          
                ├── body.html
                └── priority.txt

The base template is just like an event template, but named ``_base`` and placed
either in the
:ref:`template base <templatedesigners/structure:Overall template structure>`,
or within a :ref:`scope <keyconcepts/scopes:Notification scopes>`. Notice the underscore!

When you do that, this template will be loaded before the template of the event
to send.

How do the templates for *base* and *event* interact?

Tattler uses Jinja as default template engine, and the base template in passed to the
event template as variable ``base_template``.

The event template can then use Jinja's ``{% extends base_template %}`` keyword and
leverage `Jinja's template inheritance <https://jinja.palletsprojects.com/en/3.1.x/templates/#template-inheritance>`_.

Here's an example for the **base template**:

.. code-block:: Jinja

    {# this is _base/email/body.html #}
    <!DOCTYPE html>
    <html>
        <head>
            <title>{% block title %}Default title{% endblock %}</title>
        </head>
        <body>
        This content will be displayed in every event template that
        extends this base template.

        {% block content %}This can be overridden by
        each event template{% endblock %}

        {% block footer %}Call +41 78965432 for support.{% endblock %}
        </body>
    </html>

and here's an example for any **event template** that uses the base template:

.. code-block:: Jinja

    {% extends base_template %}
    {# this is reservation_confirmed/email/body.txt #}

    Hello {{ user_firstname }}! You might meet with any of these specialists:
    
    {% for name in specialists %}
    {{ name }}
    {% endfor %}

Nota bene:

* Adding a base template to a scope only makes it available as "opt-in" to events in the scope. Each event template defines for itself whether it uses the base template or not.
* Event templates must explicitly reference the base template when they want to extend it.
* The ``{% extends base_template %}`` tag must be at the very beginning of the event template.

Deploying base templates
------------------------

You can deploy base templates either:

- Per-scope.
- Shared among all scopes.


Shared base templates
^^^^^^^^^^^^^^^^^^^^^

The more common case is to share a base template among all scopes -- so all your applications
share the same branding. Do so by placing the ``_base`` directory directly under the template base:

.. code-block::

    templates_base/
    ├── _base/                  <- Base template shared among all scopes
    ├── mywebapp/               <-- a scope
    │   ├── password_changed/    <- an event
    │   └── order_accepted/
    └── pmtintegrator/          <-- a scope
        ├── ...


Per-scope base templates
^^^^^^^^^^^^^^^^^^^^^^^^

Alternatively, you can provide a different base template to each scope by placing the ``_base``
directory within the scope:

.. code-block::
    
    templates_base/
    ├── mywebapp/               <-- a scope
    │   ├── _base/              <- one base template for this scope
    │   ├── password_changed/    <- an event
    │   └── order_accepted/
    └── pmtintegrator/          <-- a scope
        ├── _base/              <- another base template for this scope
        ├── ...

Complex arrangements
^^^^^^^^^^^^^^^^^^^^

You can also mix and match. For example, you may want all scopes to use a shared base template,
except for one specific scope.

Simply place a ``_base`` directory within the template base, and add a different ``_base`` template within the scope as well:

.. code-block::

    templates_base/
    ├── _base/                  <- shared base template
    ├── mywebapp/               <-- a scope
    │   ├── password_changed/    <- an event
    │   └── order_accepted/
    └── pmtintegrator/          <-- a scope
        ├── _base/              <- custom base template for this scope
        ├── ...

In this configuration, the ``_base`` template in scope ``pmtintegrator`` overrides
the shared base template defined in the template base.

If you need to share a base template between multiple scopes, but not all,
you can use symbolic links to avoid duplicating the concrete ``_base`` folder:

.. code-block::

    templates_base/
    ├── _base/                  <- shared base template
    ├── _base_alternate/        <- alternate base template for few scopes
    ├── mywebapp/               <-- scope 'mywebapp' will use _base
    │   ├── password_changed/
    │   └── order_accepted/
    ├── fulfiller/              <-- scope 'fulfiller' will use _base_alternate
    │   ├── _base               <-- symbolic link to ../_base_alternate
    │   ├── order_shipped/
    │   ├── delay_occurred/
    │   └── shipping_error/
    └── pmtintegrator/          <-- scope 'pmtintegrator' will use _base_alternate
        ├── _base               <-- symbolic link to ../_base_alternate
        ├── ...
