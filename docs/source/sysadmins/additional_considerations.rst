Additional considerations
=========================

Performance
-----------

Delivery speed, latency, or overall throughput are non-goals of tattler.

That said, the bottleneck in throughput is the actual delivery to the network, via SMTP, SMS, WhatsApp or Telegram.
This may take several hundreds milliseconds per request.

In second instance, any tattler plug-in which you may have provided to load data from your database.
These may take tens- to hundreds of milliseconds, depending on your code and type of data.

The bulk of Tattler's work -- loading templates, expanding them, packaging them in a final notification --
will run within a handful milliseconds.

You may expect tattler to easily take few tens of tasks per second.
If your use case requires substantially higher throughput, look for other solutions.


Security
--------

Tattler is designed to be used by internal processes in your developers' control.
Those applications are assumed to be trusted.

For that reason, security is a non-goal.

If you run tattler on a server that hosts non-trusted users, make sure you restrict access to its port
to trusted applications.
