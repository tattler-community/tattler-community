Context plug-ins
================

Context plug-ins extend or override :ref:`context variables <keyconcepts/events:Context>` passed to templates.

You may have an arbitrary number of context plug-ins, e.g. to load information about billing,
account status, support tickets etc.

Each context plug-in can indicate whether it should be loaded based on the content of the current context.
This enables them to "fire" based on the event being notified, or the recipient, or more.

.. note:: The class for context plugins was renamed in Tattler version 1.2.0 .

    Up until Tattler version 1.1.1 you would inherit from class
    ``ContextTattlerPlugin`` in order to define a context plug-in.

    Since Tattler version 1.2.0, the class was renamed to
    :class:`ContextPlugin <tattler.server.pluginloader.ContextPlugin>`
    for simplicity and symmetry with
    :ref:`Addressbook plug-ins <plugins/addressbook:Addressbook plug-ins>`.

    Name ``ContextTattlerPlugin`` is still available as an alias for
    backward compatibility, but you'll get a deprecation notice when
    plug-ins inheriting from it are loaded.


Writing a context plug-in
-------------------------

Context plug-ins are python files that

- are placed in the :ref:`plug-in directory <configuration:TATTLER_PLUGIN_PATH>`,
- implement the ``ContextPlugin`` interface of class :class:`tattler.server.pluginloader.ContextPlugin`.

Plug-in filenames **must** end with ``_tattler_plugin.py``; other filenames are ignored.

To create a context plug-in:

1. Familiarize yourself using the :ref:`quickstart example <quickstart:Write a context plug-in>`.

2. Start coding your own starting with the `sample plug-ins <https://github.com/tattler-community/tattler-community/blob/main/plugins/>`_ in Tattler's repository.

See :ref:`Deploying plug-ins <sysadmins/deploy_plugins:Deploy custom plug-ins>` for tips on deployment.


Supplying attachments
---------------------

A context plug-in can attach files (inline images, PDFs, etc.) to outgoing emails by
populating the reserved ``_attachments`` context key. The shape is the same as the
:ref:`HTTP wire format <developers/api_http:Sending attachments>`, with one
plug-in-only convenience: payloads can be passed as raw ``bytes`` via ``content_bytes``
instead of base64 strings.

.. code-block:: python

    from tattler.server.pluginloader import ContextPlugin


    class BrandingTattlerPlugin(ContextPlugin):
        def process(self, context):
            attachments = dict(context.get('_attachments', {}))

            # inline image -- key is the cid (must contain '@')
            attachments['logo@brand'] = {
                'content_bytes': self._load_logo_bytes(),
            }

            # regular attachment -- key is the filename
            attachments['terms.pdf'] = {
                'url': 'https://internal/legal/terms.pdf',
            }

            context['_attachments'] = attachments
            return context

A few things to know:

* **Disambiguation by key shape.** A key containing ``@`` is the Content-ID of an
  inline image, referenced from HTML as ``<img src="cid:logo@brand">``. A key without
  ``@`` is the filename of a regular attachment, and the file extension drives the
  MIME type (so use real filenames like ``invoice.pdf``, not ``file1``).
* **Pipelining.** When several context plug-ins are configured, a later plug-in sees
  the attachments accumulated by earlier plug-ins. Always copy the dict before
  mutating it (``dict(context.get('_attachments', {}))``) so you don't accidentally
  mutate state owned by a sibling plug-in.
* **Type detection for inline images.** Tattler auto-detects PNG, JPEG, GIF, WebP, and
  SVG from the bytes. You don't (and can't) supply a ``filename`` for inline entries;
  if your bytes aren't one of those formats, the notification fails with a clear error.
* **Size limit.** The total raw size of attachments per email is capped at 7 MB. Plug-ins
  hitting the cap should consider linking to the file from the email body instead.
