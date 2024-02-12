.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

Tattler enterprise
==================

Tattler offers an enterprise subscription to suit the need of commercial organizations
for continuity and support.

.. hint:: Getting onto a tattler enterprise subscription is totally optional!

    Tattler is open-source software, and its liberal BSD license allows unlimited
    personal and commercial use.

    A tattler enterprise subscription is an option available to organizations
    that want to either give back, or get guaranteed maintenance and extra features.

Organizations who opt to go onto an enterprise subscription get:

- A bug-fixing guarantee: we'll fix any bug you report in an expedite fashion.
- Level-3 troubleshooting support from our development team in case of issues.
- The confidence of ensuring the longevity of the project.

Enterprise customers also get access to *tattler enterprise edition* -- a distribution of
tattler that includes a couple of additional features:

- Delivery to `Telegram <https://telegram.org>`_ and `WhatsApp <https://www.whatsapp.com>`_.
- Multilingual support: automatically send which language a user should be notified with.
- Rate control: prevent faulty applications from flooding users with notifications.
- Auto-text: design HTML emails only, Tattler automatically creates text-form fallback.

We are grateful to enterprise customers for securing the project's sustainability and
quality the benefit of all.

In addition to enterprise subscriptions, commercial users may opt to become *tattler sponsors*,
which includes everything an enterprise subscription offers, plus the additional perk of
having your company featured as a sponsor on our website and documentation.

Find further information on commercial use on `tattler's website <https://tattler.dev/#enterprise>`_,
and write to ``enterprise at tattler.dev`` for further information such as invoicing, terms, support etc.


Upgrading to Tattler enterprise
-------------------------------

Once you got onto an enterprise subscription, guaranteed maintenance and access to support is given.

You may additionally opt to switch to running *tattler enterprise edition*, a special distribution of
tattler that includes some extra features.

Switching to running tattler enterprise edition is wholly optional:

Benefits:

- Extra features.

Drawbacks:

- If you terminate your tattler subscription, you'll want to switch back to community edition.

.. note:: We do not require former enterprise supporters to downgrade! But you'll likely want to.

    We are grateful to any organization supporting tattler with a subscription -- even for one month.
    You terminating your subscription in no way affects our gratitude -- and we are happy if you
    keep using tattler enterprise edition thereafter 🙂

    However, after your enterprise subscription expires, so will credentials to the package repository
    hosting enterprise edition, which will prevent you from getting updates.

    Because of that, you'll likely want to downgrade to tattler-community to stay on a maintained
    codebase with resolution to bugs and security updates.


Upgrade process
^^^^^^^^^^^^^^^

Have you decided to switch to tattler enterprise edition?

Proceed as follows:

1. Start an `enterprise subscription on tattler's website <https://tattler.dev/#price>`_ .

2. Drop us a line at ``enterprise at tattler.dev`` to tell us you'd like access to tattler enterprise edition.

3. Within a few days we'll send you access credentials to the private package repository of tattler enterprise edition.

3. Use your new credentials to install tattler enterprise edition:
    .. code-block:: bash

        pip install --index-url https://pypi.tattler.dev/projects/ tattler

Tattler enterprise edition is a drop-in replacement to Tattler community edition.

It is a strict superset of its features, and supports the same filesystem structure
for event templates.


Downgrade process
-----------------

If you terminate your enterprise subscription, your credentials to the package repository
for tattler enterprise edition expires.

You are welcome to keep using your deployed enterprise edition. However, you'll likely want
to switch back to tattler-community to stay on a maintained code base -- in particular for
security updates.

Downgrading will lose you access to the extra features of tattler enterprise, but
does not require any other adaptation on your side.

To replace your tattler enterprise edition with tattler community edition, do as follows:

.. code-block:: bash

    # load the virtual environment where you installed tattler
    . ~/tattler_quickstart/venv/bin/activate

    # uninstall the currently-installed enterprise edition
    pip uninstall -y tattler

    # install the public community edition
    pip install tattler
