# 2.1.0 -- 2024-11-25

- When an addressbook plug-in provides a first name, pass that to `user_firstname` template variable of guessing it from email
- Improve `send()` interface to deliver details of notification failures such as SMTP AUTH errors
- Better document Python client SDK for looking up scopes and events onto tattler server.

# 2.0.1 -- 2024-06-25

- Fix failure to deliver email notification if it's plain-only and contains special characters
- Fix tattler prioritizing old-style template format to new-style if both co-existed

# 2.0.0 -- 2024-06-13

- Add tattler_livepreview to assist template editors with automatic expansion and delivery upon save.
- Rename template files to simplify editing: body and body_plain -> body.txt, body_html -> body.html, subject -> subject.txt, priority -> priority.txt . The old naming is still supported until v3.0, but will log deprecation messages.
- Automatically detect if a common ``_base`` is shared among all scopes, help directly in the template base directory.

# 1.5.2 -- 2024-04-16

- Support sending complex context data using JSON files in `tattler_notify`.
- Support TATTLER_SMTP_TIMEOUT envvar to control SMTP timeout (default 30s).
- Automatically detect when SMTP connection should be TLS based on target port.

# 1.5.1 -- 2024-03-04

- Configure client endpoint programmatically, default to `127.0.0.1:11503`.

# 1.5.0 -- 2024-02-20

- Support running on python 3.9, from good old 2020.
- Support multiple SMS sender IDs.
- Support mobile numbers with '00' prefix when operating without addressbook plug-ins.

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

- Ship with Jinja as default template engine to simplify installation and docs.
- Context plug-ins now inherit ContextPlugin class.
- Renamed demo notification to `demoscope`/`demoevent` (from `sample`).
- Improved documentation, now broken down into sections.
- Added ready-to-use examples for plug-ins that query SQL database.

# 1.1.1 -- 2024-01-14

- Fix built-in demo failing to build the sample SMS template.
- Some rearrangement of the codebase to keep as much of tattler-enterprise as possible in tattler-community too.

# 1.1.0 -- 2023-12-31

- Move SMS templates from event/sms to own subfolder event/sms/body.
- Clearly annotate features specific to enterprise edition in docs.

# 1.0.0 -- 2021-10-31

- Initial release
