HTTP API
--------

You open a TCP socket and send a HTTP POST request to tattler_server.

This API allows you to:

* Trigger notifications.
* List scopes.
* List events within a scope.
* List vectors for an event.

See the interactive `OpenAPI spec <https://tattler.dev/api-spec/>`_ for details.


Sending attachments
^^^^^^^^^^^^^^^^^^^

Email notifications can carry inline images (referenced from the HTML body via ``cid:``)
and regular file attachments. Both are supplied in the same JSON body as your context
variables, under the reserved ``_attachments`` key:

.. code-block:: json

    {
      "user_firstname": "Alice",
      "_attachments": {
        "logo@brand":  {"content_b64": "iVBORw0KG..."},
        "invoice.pdf": {"url": "https://internal.example.com/invoices/123.pdf"}
      }
    }

The dict-key format itself disambiguates the two kinds of attachment:

* A key containing ``@`` is a **Content-ID** for an inline image. Reference it from your
  HTML body as ``<img src="cid:logo@brand">``. Tattler auto-detects the image format
  from the bytes (PNG, JPEG, GIF, WebP, SVG); no ``filename`` field is needed.
* A key without ``@`` is the **filename** of a regular attachment. The MIME type is
  derived from the filename's extension (so use a meaningful name like ``invoice.pdf``,
  not ``file1``). Unknown extensions are rejected.

Each entry must specify exactly one of:

``url``
    Tattler fetches the file over HTTP/HTTPS. Follows up to 5 redirects, with a 3 s
    connect timeout and 20 s per-chunk read timeout.

``content_b64``
    The bytes of the file, base64-encoded. Suitable for files you already have in
    memory.

Failures (oversize attachment, unknown image format, malformed base64, fetch errors,
etc.) cause the notification request to fail with HTTP 4xx/5xx. Tattler will not silently
drop a requested attachment.


Limits
""""""

* Maximum total size of attachments per email: **7 MB** (raw, before base64 encoding).
  This headroom matches the typical 10 MB cap of SMTP relays once base64 inflation is
  factored in.
* Maximum HTTP request body size: **12 MB** (~7 MB of attachments + base64 overhead +
  slack for the rest of the JSON payload). Requests exceeding this are rejected with
  HTTP 400 before the body is read.

These limits are not configurable. If you regularly need to send larger files, consider
hosting them externally and including a download link in the email body instead.


Trust model
"""""""""""

Tattler's HTTP listener has no authentication: anyone who can reach the port can submit
attachments, including URL-fetch entries. **Tattler treats the caller as trusted** and
does not perform SSRF protection — internal URLs, ``localhost``, presigned S3 links and
internal CDNs all work without configuration. Make sure the listener is reachable only
from systems you trust (firewall, private network, mTLS, etc.).

Only ``http`` and ``https`` URL schemes are accepted; ``file://`` and other schemes are
rejected.


