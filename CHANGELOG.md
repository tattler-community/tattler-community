# 1.5.0 -- TBD

- extend compatibility to python 3.9
- accept international prefix in '00' form in passthrough addressbook
- improve validation hints in clients from cmdline and python SDK

# 1.4.0 -- 2024-02-12

- Include new README with screenshots, better description, quickstart, contributing infos and links.
- Add 'user_id' variable to native template context.
- Streamline python package by removing superfluous docs sources, now moved to repo root.

# 1.3.0 -- 2024-02-10

- Fix regression from 1.2.0 preventing loading of templates.
- Fix regression from 1.2.0 where priority of HTML content causing some clients to favor plain text display.
- New demo notification packed with useful tips and reusable style/elements for your own templates.
- Support hostnames in TATTLER_SMTP_ADDRESS envvar.

# 1.2.0 -- 2024-01-20

- ship with Jinja as default template engine to simplify installation and docs
- Context plug-ins now inherit ContextPlugin class
- Renamed demo notification to `demoscope`/`demoevent` (from `sample`)
- Improved documentation, now broken down into sections
- Added ready-to-use examples for plug-ins that query SQL database

# 1.1.1 -- 2024-01-14

- fix built-in demo failing to build the sample SMS template
- some rearrangement of the codebase to keep as much of tattler-enterprise as possible in tattler-community too

# 1.1.0 -- 2023-12-31

- move SMS templates from event/sms to own subfolder event/sms/body
- clearly annotate features specific to enterprise edition in docs

# 1.0.0 -- 2021-10-31

- initial release
