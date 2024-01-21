.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

Upgrading to Tattler enterprise
===============================

What and why
------------

Tattler offers an enterprise subscription to suit the need of commercial organizations
for continuity and support.

We -- in turn -- use the proceeds to safeguard the continuity and quality of the project.

Check out Tattler's website for a description of `what you get with an enterprise
subscription <https://tattler.dev/#enterprise>`_.

Upgrade process
---------------

Proceed as follows:

1. Start an enterprise subscription on `tattler's website <https://tattler.dev/#price>`_ .

2. Within 24 hours you receive an email with your access credentials.

3. Install tattler enterprise edition with your new access credentials:
    .. code-block:: bash

        pip install --index-url https://pypi.tattler.dev/projects/ tattler

Tattler enterprise edition is a drop-in replacement to Tattler community edition.

It is a strict superset of its features, and supports the same filesystem structure
for event templates.

Downgrade process
-----------------

If you terminate your enterprise subscription, your access to tattler enterprise
edition terminates with it.

Downgrade to the Tattler community edition to stay on a maintained code-base,
in particular security updates.

Downgrading will lose you access to the extra features of tattler enterprise, but
does not require any other adaptation on your side.

Downgrade as follows:
    .. code-block:: bash

        pip uninstall -y tattler
        pip install tattler
