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



