.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

Command-line tools
==================

Tattler installs three command-line utilities:

* :ref:`tattler_server <clitools:tattler_server>` -- the notification server itself.
* :ref:`tattler_notify <clitools:tattler_notify>` -- fire a notification from the command line, e.g. from shell scripts or cron jobs.
* :ref:`tattler_livepreview <clitools:tattler_livepreview>` -- preview template edits live in your own mailbox while designing them.

tattler_server
--------------

.. program:: tattler_server

Run the tattler notification server:

.. code-block:: bash

   tattler_server

``tattler_server`` takes no command-line arguments: it is configured entirely through
environment variables, such as :ref:`TATTLER_TEMPLATE_BASE <configuration_template_base>`
and ``TATTLER_LISTEN_ADDRESS``.

See :doc:`configuration` for the full list of supported variables, and
:doc:`sysadmins/index` for deployment guidance.

tattler_notify
--------------

Send a notification through a running tattler server. For example:

.. code-block:: bash

   tattler_notify -s 127.0.0.1:11503 -m production user@example.com mywebapp password_changed

.. argparse::
   :module: tattler.client.tattler_py.tattler_cmd
   :func: build_parser
   :prog: tattler_notify

tattler_livepreview
-------------------

Edit a notification template and receive the resulting notification in your mailbox
each time you save -- see :doc:`testing/livepreview` for a walk-through. For example:

.. code-block:: bash

   tattler_livepreview ~/mytemplates

.. argparse::
   :module: tattler.server.tattler_livepreview
   :func: build_parser
   :prog: tattler_livepreview
