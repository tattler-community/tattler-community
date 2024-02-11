Base templates
--------------

You usually want to send notifications with a consistent style. Especially for HTML,
where you want to have a common design -- colors, fonts, footer links etc.

But often also for plain-text, where you might want to include disclaimer footers.

The tools you learned so far enable you to do that, but you'd repeat those common
elements in every single event template.

Tattler supports **base templates** to simplify that::

    templates_base/
    └── mywebapp/                       <-- a scope
        ├── _base                       <- base template (NB: _base )
        │   └── email/                  <- base template for email
        │       ├── subject             
        │       ├── body_plain          
        │       ├── body_html
        │       └── priority
        └── reservation_confirmed/      <- event template
            └── email/
                ├── subject             
                ├── body_plain          
                ├── body_html
                └── priority

The base template is just like an event template, but named ``_base``. Notice the
underscore!

Place it into the same folder of your events, i.e. beneath the
:ref:`scope <keyconcepts/scopes:notification scopes>` folder.

When you do that, this template will be loaded before the template of the event
to send.

How do the templates for *base* and *event* interact?

Tattler uses Jinja as default template engine, and the base template in passed to the
event template as variable ``base_template``.

The event template can then use Jinja's ``{% extends base_template %}`` keyword and
leverage `Jinja's template inheritance <https://jinja.palletsprojects.com/en/3.1.x/templates/#template-inheritance>`_.

Here's an example for the **base template**:

.. code-block:: Jinja

    {# this is _base/email/body_html #}
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
    {# this is reservation_confirmed/email/body_plain #}

    Hello {{ user_firstname }}! You might meet with any of these specialists:
    
    {% for name in specialists %}
    {{ name }}
    {% endfor %}

Nota bene:

* Adding a base template to a scope only makes it available as "opt-in" to events in the scope. Each event template defines for itself whether it uses the base template or not.
* Event templates must explicitly reference the base template when they want to extend it.
* The ``{% extends base_template %}`` tag must be at the very beginning of the event template.

Deploying base templates
^^^^^^^^^^^^^^^^^^^^^^^^

Base templates are made available per-:ref:`scope <keyconcepts/scopes:notification scopes>`.

However, often a company style applies to notifications from all subsystems.

No worries! It's easy to share a base template across scopes with **symbolic links**::

    templates_base/
    ├── _base/                  <-- concrete base template to share
    ├── mywebapp/               <-- a scope
    │   ├── _base/              <- symbolic link to -> ../_base/
    │   ├── password_changed/    <- an event
    │   └── order_accepted/
    ├── fulfiller/              <-- a scope
    │   ├── _base/              <- symbolic link to -> ../_base/
    │   ├── order_shipped/       <- an event
    │   ├── delay_occurred/
    │   └── shipping_error/
    └── pmtintegrator/          <-- a scope
        ├── _base/              <- symbolic link to -> ../_base/
        └── cc_charge_failed/    <- an event

Simply create those as follows:

.. code-block:: bash

    cd templates_base/
    # create your actual _base template inside here
    mkdir -p _base/email/
    # create symlinks to it in every scope
    ln -s ../_base mywebapp/
    ln -s ../_base fulfiller/
    ln -s ../_base pmtintegrator/

This obviously gives you the freedom to mix and match base templates as you please.
For example, you may want to have 2 base templates, and have events from each scope
use either one of them, simply by setting the right target of the symbolic link.

