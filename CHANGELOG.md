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