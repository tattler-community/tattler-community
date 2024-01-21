Install into a virtual environment
==================================

Create a python virtual environment and let tattler run into it.

.. code-block:: bash

    # create a user for tattler and change to it
    adduser tattler
    sudo -s tattler

    # build a python virtual environment
    python3 -m venv ~tattler/venv_tattler

    # load the virtual environment
    . ~tattler/venv_tattler/bin/activate

    # install tattler
    pip install tattler

    # deploy templates
    mkdir ~tattler/tattler_templates

    # run tattler
    NOTIF_DEBUG_RECIPIENT_EMAIL=your_own_email@company.com \
        TATTLER_TEMPLATE_BASE=~tattler/tattler_templates \
        TATTLER_LISTEN_ADDRESS="127.0.0.1:11503" \
        TATTLER_MASTER_MODE="debug" \
        tattler_server

At this point, tattler will be listening on ``127.0.0.1:11503`` for requests to notify.

