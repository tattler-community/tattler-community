Provide access to template designers
====================================

The database of :ref:`Event templates <keyconcepts/events:event templates>` is a plain folder,
competently assembled by your :ref:`template designer <roles:template designers>`.

As long as you are not in production, both you and them will want to empower them to self-deploy such database:

- So you don't need to do it yourself.
- So they can iterate and test as often as they want without you being in the way.

Do so by simply providing them with filesystem access to the relevant folder, e.g. with rsync.

When you reached production, you might want to restrict this process to avoid issues like accidental removal of all templates.

You may do so by having a "shadow" template folder that template designers have access to, and then a script which runs some basic validation before syncing this folder over to the live folder.

Your validation may include:

- no scope has been removed
- no more than X% of events has been removed
- every event template is well-formed
- every template event sends successfully in debug mode

