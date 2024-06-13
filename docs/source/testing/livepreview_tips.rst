Tips on development previews
============================

Here's some tips to improve the efficiency of your editing workflow.

Livepreview, no DIY
-------------------

Do use ``tattler_livepreview`` to preview your templates.

Resist the temptation to just open your template files in a browser.

There are 3 main reasons for this: faithfulness of rendering, generation and delivery.

.. mermaid::

    flowchart LR
        template --> client --> tattler_server --> SMTP --> mailbox


Faithful rendering
^^^^^^^^^^^^^^^^^^

Your browser will deceive you.

Email programs support a much smaller subset of HTML / CSS features than browsers.
(Website `caniemail.com <caniemail.com>`_ documents this difference).
Your template might hence render beautifully in the browser and be entirely broken
when your users open it in their email application.


Faithful generation
^^^^^^^^^^^^^^^^^^^

``tattler_livepreview`` renders and delivers the email through the same code chain that
will run in production.

This includes serializing context data, issuing the request to the ``tattler_server``,
expanding the request through it, and delivering the final content to the SMTP server.

This ensures you'll find out any issues in this chain as it would occur in production.
For example, issues serializing your context data, or inconsistencies in your data types
during rendering.


Faithful delivery
^^^^^^^^^^^^^^^^^^

If any part of your content triggers some spamicity rules at your recipient server,
you are going to find out during development rather than after deployment.

This is particularly relevant for players like Gmail, that got dominant enough to
careless with false positives.


Context files as specification
------------------------------

Always provide a ``context.json`` file as part of your templates.

Their utility goes beyond being able to live-preview them.

Sample context files serve as a quick reference of a specification for the event template:

- Which variables does the template take?
- What is their concrete data type?
- If a variable is an object, what are its expected members?


Which email client to test against
----------------------------------

Check rendering with **several** email applications.

You can statistically cover 90% of your users with only 3, since here's an estimation of
their market share as of March 2024 (Source: `oberlo.com <https://www.oberlo.com/statistics/most-used-email-clients>`_):

- 56% Apple Mail
- 30% Gmail
- 4% Outlook

Gmail is an especially good test candidate, because it has some of the
`poorest support for HTML emails <https://www.caniemail.com/scoreboard/>`_,
and coarse in tagging emails as spam.


A/B comparisons
---------------

Work your templates keeping your email application side-to-side with your editor.

While editing, only save your template when you want a preview generated.

Keep older notifications during development, so you can quickly do A/B comparisons
of alternative presentation formats as you implement them.

Clear preview emails from your mailbox only when you are done editing.


Separate mailbox for template design
------------------------------------

It's often useful to have a separate mailbox for developing templates,
say ``dev-notifications@company.com``.

This allows you e.g. to share access to it among multiple developers, avoid
littering your own mailbox, or freely forward notifications without sharing
personal data.


