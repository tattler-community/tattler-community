Auto-text
=========

.. note:: This feature is only available in Tattler's `enterprise edition <https://tattler.dev#enterprise>`_.
    
With the auto-text feature, you only provide a ``body.html`` definition,
and Tattler automatically generates an ASCII version of that faithfully
mirrors your HTML content, including emphasis, hyperlinks, lists and tables.

Auto-text is automatically enabled in Tattler enterprise edition. All you
need to do to use it is to provide your ``body.html`` content and omit the
``body.txt`` file.

If you do provide a ``body.txt`` file in your event template, then Tattler
will skip auto-text and use the content your provided in it as plain text version.
