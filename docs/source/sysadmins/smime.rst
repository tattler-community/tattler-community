Signing with S/MIME
===================

.. note:: This feature is only available in Tattler's `enterprise edition <https://tattler.dev#enterprise>`_.

Tattler supports cryptographically signing outgoing notifications,
so users receive them with a beautiful badge ensuring they are genuine.

The security benefits usually appeal services in specific sectors, such as finance and healthcare.

However, projecting trustworthiness can benefit most brands.

Requirements
------------

Server-side, Tattler has the following requirements to perform S/MIME signing:

- ``tattler_server`` must run on a UNIX system
- ``openssl`` must be installed (version ≥ 3.0)
- You have a valid S/MIME certificate provisioned to the address configured as :ref:`TATTLER_EMAIL_SENDER <configuration:TATTLER_EMAIL_SENDER>`.

Client-side, `many email clients support S/MIME signature verification <https://gist.github.com/rmoriz/5945400>`_,
including Apple Mail, Microsoft Outlook, Mozilla Thunderbird, IBM Notes, KMail, Sony Mail Client and more.
Apple Mail alone covers over 50% of users.

Gmail notably lacks support for S/MIME signatures. Google deliberately chooses to deactivate
this feature in their free webmail, while supporting it in their commercial version. Their
webmail, which also `scores poorly in support for HTML emails <https://www.caniemail.com/scoreboard/>`_,
is used by 30% of users.


Maintenance
-----------

S/MIME certificates are usually issued with a 1-year validity, so deploying S/MIME
signatures in tattler adds the maintenance effort to renew and re-deploy this certificate.
This is roughly a 15' task once yearly.

S/MIME signing comes with no lock-in. You may decide to disable S/MIME signing anytime,
and previously sent notifications will still appear as valid.


Obtaining a S/MIME certificate
------------------------------

Many commercial vendors exist offering you S/MIME certificates for little money.
Just google for "Buy S/MIME certificate".

Multiple certificate classes exist offering increasingly extensive validation.
TLS certificates have similar grading, but those extended validation levels have
long fallen into irrelevance.

The same considerations hold for S/MIME certificates, with the added factor that the
additional levels are even less perceivable by the user.

All in all, class 0 (mailbox validation) is all you need.


Free S/MIME certificates
^^^^^^^^^^^^^^^^^^^^^^^^

In the 2010s several vendors issued S/MIME certificates free of charge.

As of 2024, `Actalis <https://extrassl.actalis.it/portal/uapub/freemail?lang=en>`_ is the only
vendor offering **free S/MIME certificates**.

Their certificate has the same quality as paid certificates, and is indistinguishable
by the user. A paid certificate gives you:

- The ability to generate the private key yourself. The Actalis free offering generates the private key for you, which is a deal-breaker in security-critical scenarios.
- Some extra peace of mind of knowing that your vendor is more likely to still be an option when the certificate expires.

You might wonder if LetsEncrypt offers you S/MIME certificates. They deliberately
chose not to, mostly because they found it difficult to securely validate mailboxes.
This might change in the future.


Configuration
-------------

Take the S/MIME certificate as it was provided to you by your vendor, and export the private key and
the certificate data into a `.pem` file.

If you your S/MIME certificate in a PKCS-12 called `mycrt.p12`, here's how you convert it to PEM::

    openssl pkcs12 -in mycrt.p12 -out mycrt.pem -noenc

If this file is encrypted, like they usually are, ``openssl`` will prompt you for the decryption password.

The ``-noenc`` option is important here. If omitted, ``openssl`` will ask you for one more password to
encrypt your output private key. This will prevent ``tattler_server`` from getting your private key,
necessary for signing.

If you have them as separate PEM files, combine them together by placing the private key content
before the certificate content.

Then give tattler configuration key :ref:`TATTLER_EMAIL_SMIME_CERT <configuration:TATTLER_EMAIL_SMIME_CERT>`,
set to the path of the PEM file.

.. warning::
    Make sure the user running ``tattler_server`` has permission to open this PEM file (and traverse all directories above it).

    And also make sure that nobody else can, since this file PEM holds sensitive data (your private key).


Validation
----------

You may validate that S/MIME signatures are being applied both on the server and the client.

Server-side, ``tattler_server`` will log when signing outgoing email notifications::

    [INFO] Signing email notification from foo@organization.org .

If ``tattler_server`` encounters any issue with your configuration, it will log details::

    [WARN] TATTLER_EMAIL_SMIME_CERT path '/home/tattler/certs/support-organization-org.pem'
        appears to be binary. I need a PEM file that includes 'BEGIN PRIVATE KEY' and
        'BEGIN CERTIFICATE' sections.

Client-side, you may open the outbound notification from a client supporting S/MIME,
such as Apple Mail or Microsoft Outlook, and look for the badge.
