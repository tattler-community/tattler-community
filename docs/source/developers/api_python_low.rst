Low-level Python API
--------------------

Use this API if you need fine-grained control of notifications, for example if you want to
send a large number of notifications in one go and want to reuse the HTTP connection.

.. code-block:: python

    from tattler.client.tattler_py import TattlerClientHTTP

    # refer to templates in folder template_base/my_application. Debug mode = only send to test address, not to actual recipient
    n = TattlerClientHTTP(scope_name='myapplication', srv_addr='127.0.0.1', srv_port=11503, mode='debug')
    # send notification for event 'my_event' over email only to user #20 (tattler resolves actual email address)
    n.send(vectors=['email'], event='my_event', recipient='20')

    # send template which requires expanding variables
    n.send(vectors=['email'], event='my_event', recipient='20', context={'var1': 'value1', 'var2': 'value2'})

    # set priority flag, and use correlationID to associate throughout delivery chain
    n.send(vectors=['email'], event='my_event', recipient='20', priority=True, correlationId='12398724')

    # utility to generate correlationIds
    from tattler.client.tattler_py import mk_correlation_id
    print(mk_correlation_id())
    # NkvgXrYI

TattlerClient
+++++++++++++

:class:`tattler.client.tattler_py.TattlerClientHTTP` is the concrete HTTP-based implementation of the interface
:class:`tattler.client.tattler_py.TattlerClient`, and leverages the REST endpoint of tattler server.

.. autoclass:: tattler.client.tattler_py.TattlerClientHTTP

.. autoclass:: tattler.client.tattler_py.TattlerClient
    :members: __init__, scopes, events, vectors

Correlation IDs
+++++++++++++++

If you pass a `correlationId` to notification calls, tattler will include that string in all log messages relevant to that call.
This is purely optional, and enables you to trace a user or session across multiple subsystems of your overall service.

A `correlationId` is any string -- but preferably a unique one. You may choose to prefix this string with the name of the subsystem
where the session you want to track has originated.

Tattler offers the :func:`mk_correlation_id` symbol for that:

.. autofunction:: tattler.client.tattler_py.mk_correlation_id

