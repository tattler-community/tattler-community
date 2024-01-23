Multilingual notifications
---------------------------

.. note:: This feature is only available in Tattler's `enterprise edition <https://tattler.dev#enterprise>`_.

Need to send notifications in multiple languages? Tattler helps you do that easily:

- You define the event template for each language.
- Tattler looks up the language preference for the recipient, collects the template for that language, and delivers it.

Each language is a sub-folder placed inside of the event vector (e.g. ``email``) and named after the language code (e.g. ``de``)::

    templates_base/
    └── mywebapp/
        └── password_changed/
            └── email/                  <- E-mail vector
                ├── de/                 <- Event template for "de" language
                │   ├── body_plain
                │   ├── body_html
                │   └── subject
                └── en/                 <- Event template for "en" language
                    ├── body_plain
                    ├── body_html
                    └── subject

Simply put each translation into its own language subfolder like it were its own event.

What naming standard should these language folders follow? They may be called ``en``, ``en_US`` or else.
Tattler does not really care -- it simply looks up whatever string the
:ref:`addressbook plugin <plugins/addressbook:addressbook plug-ins>` delivers as language preference for the
user.

Speak to your :ref:`developers <developers/index:developers>` to clarify that. They are the ones to define this
when they extend the :ref:`addressbook plugin <plugins/addressbook:addressbook plug-ins>` to enable
multilingual notifications.

Default language
^^^^^^^^^^^^^^^^

Do you want to define a "default language" to use when a user has not indicated a language preference?

.. note:: Support a default language or not?

    A default language is one you communicate with when you **do not know** the user's language preference.

    Can this happen in your context? What are the consequences? Will those users understand
    your communication?

    All this is for you to decide. Speak with your :ref:`product managers <productmanagers:Product managers>` to understand the implications
    in the market, and to your :ref:`developers <developers/index:developers>` to understand what your systems store and can deliver.

    If it is, tattler allows you to support the scenario easily. However, providing
    event templates for a "default language" is by no means required, nor necessarily recommended.

    Most of your users will either prefer one language or be unable to understand the others altogether.
    
    This usually makes multilingualism an all-or-nothing endeavor: if you do support multiple languages,
    then you write **all** your content -- including notifications -- in **all** your supported languages,
    and you know the language preference for **every** user.

If you do decide to define a "default language" notification, simply put the respective definition
directly into the event template folder -- like you learned to do for the mono-lingual case::

    templates_base/
    └── mywebapp/
        └── password_changed/
            └── email/                  <- E-mail vector
                ├── body_plain          <-\
                ├── body_html           <--| event template for default language, i.e. unknown language preference
                ├── subject             <-/
                ├── de/                 <- Event template for "de" language
                │   ├── body_plain
                │   ├── body_html
                │   └── subject
                └── en/                 <- Event template for "en" language
                    ├── body_plain
                    ├── body_html
                    └── subject

How to avoid duplicate definitions for a language -- one for the language code and one for the default language?
Use symbolic links. Define the event templates for the default language in the event folder, and then create a language
folder as a symbolic link to its parent:

.. code-block:: bash

    cd templates_base/mywebapp/password_changed/email/
    ln -s . en

This makes your templates structure look like this::

    templates_base/
    └── mywebapp/
        └── password_changed/
            └── email/                  <- E-mail vector
                ├── body_plain          <- Default language
                ├── body_html
                ├── subject
                └── en/ -> ./           <- symlink "en" to .. default language

