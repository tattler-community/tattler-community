.. tip:: Found anything unclear or needy of further explanation? Do send us the feedback at `docs@tattler.dev <mailto:docs@tattler.dev>`_ !

System administrators
=====================

Your role:

- Install, configure, and run tattler.
- Keep it secure, including software updates.
- Keep it running.
- Keep it reachable by other systems.
- Deploy templates provided by :ref:`template designers <roles:template designers>`, or provide them with a way to do so themselves.
- Provision plug-ins if any is required.

Components
----------

A tattler deployment looks like this:

.. include:: ../diagrams/deployment.mermaid


.. toctree::
    install_venv
    base_config
    update_templates
    deploy_plugins

Deployment path
---------------

We proceed as follows:

1. Install into a virtual environment.

2. Provide a base configuration.

3. Provide access to template designers.

4. Deploy custom plug-ins.
