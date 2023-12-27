Template designers
==================

Your role:

- Write templates for each event.
- Design and implement the style of HTML email notifications.
- Review all that with your product manager.

You are supposed to have received (or made yourself?) a
:ref:`list of events like so <productmanagers:the table>`, which includes:

- The list of events.
- What vectors each event should be sent to.

Overall template structure
--------------------------

Templates are collected under a single folder, called :ref:`TATTLER_TEMPLATE_BASE <configuration:TATTLER_TEMPLATE_BASE>`.

Get used to where it is, because you'll spend the bulk of your time inside it over the next few weeks 😉

Scopes
^^^^^^

The :ref:`TATTLER_TEMPLATE_BASE <configuration:TATTLER_TEMPLATE_BASE>` folder contains one sub-folder for each
:ref:`scope <keyconcepts:notification scopes>`.

And each scope-folder contains events for that scope.
If scopes confuse you, define them later, together with your :doc:`developer <developers>`.

You can start by wrapping all events into one single scope -- say "mywebapp" -- so your
``TATTLER_TEMPLATE_BASE`` folder structure would look like this:

.. code-block:: text
    
    templates_base/
    ├── mywebapp/                       <-- a scope
    └── my_booking_sys/                 <-- another scope

Events
^^^^^^

Events are folders within a scope. So once you create forlders -- under your scope "mywebapp" --
for the events your fantasy :ref:`product manager <productmanagers:the table>`, your ``TATTLER_TEMPLATE_BASE``
would look like this:

.. code-block:: text

    templates_base/
    └── mywebapp/                       <-- a scope
        ├── reservation_confirmed/      <- an event
        └── password_changed/           <- another event

Vectors
^^^^^^^

Each event may require being sent over email and SMS.

Your :ref:`product manager <productmanagers:the table>` told you which event needs to be sent
with which vector:

- ``reservation_confirmed``: email only.
- ``password_changed``: email and SMS.

We'll now proceed to build those.

SMS templates
-------------

SMS notifications are less common than email notifications, but let's start here because
their simplicity builds a base to understand the more complex emails.

Event templates are some text which gets expanded at delivery time into the final text.

SMS templates are one single file inside the event's folder:

.. code-block:: text

    templates_base/
    └── mywebapp/
        └── password_changed/
            └── sms                 <- sms template

This SMS template file may contain some content like this::

    Hi {{ user_firstname }}. Be advised that your account password got changed today at {{ appointment_time }}. The address is {{ update_time }}.

You already picture what the user will actually be texted.

For SMS, that's all you need, because the SMS
:ref:`vector <keyconcepts:notification vectors>` neither supports nor requires anything more.


Email templates
---------------

Read `SMS templates`_ first as this builds upon it.

An email has multiple parts at play:

- a subject
- a body
- potentially a HTML version of the body
- potentially a priority

Email templates collect each of those parts in a separate template file. All
such files are enclosed into an ``email`` folder::

    templates_base/
    └── mywebapp/                       <-- a scope
        └── password_changed/           <- an event
            └── email/                  <- email vector
                ├── subject             <- mandatory
                ├── body_plain          <- mandatory
                ├── body_html
                └── priority

The files have the following purpose:

``subject``
    Mandatory. Contains template text which will be expanded with template variables to generate the subject of the email to send.

``body_plain``
    Mandatory. Contains template text which will be expanded with template variables to generate the body of the email to send.
    This is the plain-text body standard in every email. If a ``body_html`` file is also provided, this content only serves as a "fallback" for recipients who lack support for HTML emails.

``body_html``
    Optional. Contains template text which will be expanded with template variables to generate the HTML version of the email to send. If the recipient's e-mail application supports HTML emails, they will
    view this content first.

``priority``
    Optional. Contains an integer ∈ { 1, 2, 3, 4, 5 }, where ``1`` is "highest" and ``3`` is "normal" priority.
    Priority is implemented by setting the ``X-Priotity`` header in the final email to the user,
    so its potency depends on whether the user's email application supports that attribute -- which many do.

HTML Emails
-----------

HTML emails are plain-text emails with an HTML file attached.

Your job is to write the template for that HTML file.

Tattler's job is to expand the template and assemble the email with subject,
plain-text part and HTML part.

Write the HTML template into file ``body_html``. Make it valid HTML enclosed in
a ``<html></html>`` element:

.. code-block:: html

    <!-- this is the content of file body_html -->
    <html>
        <body>
            <h1>Password changed!</h1>

            <p>Dear {{ user_firstname }},</p>

            <p>Someone (presumably you) changed the password to your account today at  {{ appointment_time }}.</p>
        </body>
    </html>

Hold your HTML
^^^^^^^^^^^^^^

Tattler supports all the HTML you want, but email clients don't.

Some email clients don't support HTML at all -- in which case your recipient will only see
the content you prepared in ``body_plain``.

Clients that do support HTML emails do so limitedly and inconsistently.

Avoid JavaScript. Basic CSS is often supported. Refer to the excellent
`CanIEmail <https://www.caniemail.com>`_.

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
:ref:`scope <keyconcepts:notification scopes>` folder.

When you do that, this template will be loaded before the template of the event
to send.

How do the templates for *base* and *event* interact?

If you use Jinja as template engine -- as seen at :doc:`installation <quickstart>`,
then the base template in passed to the event template as variable ``base_template``.

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

Base templates are made available per-:ref:`scope <keyconcepts:notification scopes>`.

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

Email priority
--------------

Many email clients support setting and viewing an email *priority*.

These include Thunderbird, Gmail, Outlook and Apple mail.

tattler allows you to set an email's priority by placing the ``priority`` file
into the email template folder:

.. code-block:: bash

    cd templates_base/password_changed/email/
    echo "1" > priority

This will make the message "high-priority" when the user's email application supports
the feature.

Setting this file makes sense with only 2 values:

* ``1`` for "high priority"
* ``5`` for "low priority"

Value ``3`` (normal priority) is a non-action, and the values inbetween are not meaningful.

Setting messages as high-priority raises the visibility of the notification in the user's mailbox,
which loads notification fatigue even further -- so use it sparingly. A case where high-priority
makes sense is when the notification is important and also time-critical action.

Template variables
------------------

Variables can come into templates from 3 places:

1. **tattler variables** -- available in every notification.
2. **client variables** -- availabile based on what and when the application sends it. Usually one event always receives the same set of variables.
3. **plug-in variables** -- may be a mixture of the two above.

This origin plays no role in the template itself, but you need to know the origin
to know when you can use a variable.

This section lists **tattler variables**. For client variables and plug-in variables,
speak with your :ref:`application developer <roles:application developers>`.


user_email
^^^^^^^^^^

Type: str | None

E-mail address of the user being notified.


user_sms
^^^^^^^^

Type: str | None

Mobile number of the user being notified.


user_firstname
^^^^^^^^^^^^^^

Type: str

Firstname, guessed from email addressed.

The guessing is surprisingly reliable:

- Many users actually use their full name, like ``john.doe@company.com`` or ``thomas.mueller@gmail.com``.
- Heuristics are in place to avoid indeterminate traps like ``info@``. String ``user`` is provided in this case.
- Users like ``jdoe@`` can still make sense of their greeting and understand they are themselves to blame.


This logic may still be overridden by an addressbook plug-in to produce a reliable first name.
Speak to your :ref:`application developer <roles:application developers>`.


user_account_type
^^^^^^^^^^^^^^^^^

type: str | None

The name of the account type this user is on. This is always ``None`` unless provided by an addressbook plug-in.
Speak to your :ref:`application developer <roles:application developers>`.

This is useful e.g. to build conditional text and address paying and free users in different ways.


correlation_id
^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^

Type: str

A unique identifier for the notification.

A user may spell out this string for the support team to identify what notification they are referring to.

This notification_id will also be logged into tattler log files, so it can be used to get to the
`correlation_id`_, which can be then used for root-cause analysis.

This provides a clear separation of user-facing information vs internal information.


notification_mode
^^^^^^^^^^^^^^^^^

Type: str

Which :ref:`notification mode <keyconcepts:notification mode>` the notification was sent with.


notification_vector
^^^^^^^^^^^^^^^^^^^

Type: str

Name of the vector which is being sent. The template designer usually knows already, but this may be useful
in some advanced templating scenarios.


notification_scope
^^^^^^^^^^^^^^^^^^

Type: str

Name of the scope of the event.


event_name
^^^^^^^^^^

Type: str

Name of the event itself.
