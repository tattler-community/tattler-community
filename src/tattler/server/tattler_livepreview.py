"""Monitor template files and trigger respective notification when one changes"""

from datetime import datetime
import logging
import getpass
import os
import stat
import sys
import tempfile
import time
import json
from typing import Mapping, Any, AbstractSet, Tuple
from pathlib import Path

import jinja2

from tattler.server.templatemgr import TemplateMgr, get_scopes
from tattler.server.tattler_utils import get_template_processor, replace_time_values, obfuscate, unobfuscate, setenv
from tattler.server.sendable import make_notification, send_notification

logging.basicConfig(level=logging.DEBUG, format='%(message)s', force=True)
log = logging.getLogger(__name__)

conf = {}

file_change_poll_interval_s = 0.25

def get_input(prompt: str) -> str:     # pragma: no cover
    """Mocked input() builtin"""
    return input(prompt)

def get_user_input(prompt: str, private: bool=False) -> str:
    """Collect input from user, either publicly or privately"""
    if private:
        return getpass.getpass(prompt + '[hidden input] ')
    return get_input(prompt)

def template_files(template_base: Path) -> AbstractSet[Path]:
    """Return the set of template files within a folder.
    
    :param template_base:   Pathname of the templates directory, expected to hold scopes and event templates within it.
    :return:                Set of template files to watch within the template_base.
    """
    def depth(p: Path, base: Path) -> int:
        d = 1
        parent = p.parent
        while parent != base:
            parent = parent.parent
            d += 1
        return d
    if not template_base.is_dir():
        raise FileNotFoundError(f"Template base {template_base} is not a directory")
    # actually return template files
    wanted_filenames = ['body.txt', 'body.html', 'subject.txt', 'priority'] + ['body_html', 'body_plain', 'subject']
    wanted_files = set()
    for wfile in wanted_filenames:
        wanted_files |= {f for f in template_base.glob(f'**/email/{wfile}') if depth(f, template_base) == 4}
    return wanted_files

def get_event_coordinates(template_filename: Path) -> Tuple[str, str]:
    """Extract the event name from a template filename.
    
    :param template_filename:   Pathname of the template file.
    :return:                    event_name, scope_name that the template file belong to.
    """
    return template_filename.parent.parent.name, template_filename.parent.parent.parent.name


def files_changed(template_base: Path) -> AbstractSet[Path]:
    """Monitor a set of files and return when some are written into.
    
    :param template_base:   Pathname of the templates directory, expected to hold scopes and event templates within it.
    :return:                Set of one or more paths that underwent change
    """
    mtimes = {}
    modified = set()
    prev_files = template_files(template_base)
    log.info("\nNow waiting for changes on %s files. Press Ctrl-C to interrupt.", len(prev_files))
    while prev_files:
        monitored_events, monitored_scopes = zip(*[get_event_coordinates(f) for f in prev_files])
        monitored_events, monitored_scopes = set(monitored_events), set(monitored_scopes)
        cur_files = template_files(template_base)
        if cur_files - prev_files:
            log.warning("Template files added: %s", cur_files - prev_files)
            modified |= cur_files - prev_files
        if prev_files - cur_files:
            log.warning("Template files deleted: %s", cur_files - prev_files)
        for f in cur_files:
            mtime = f.stat().st_mtime
            if str(f) not in mtimes:
                mtimes[str(f)] = mtime
            elif mtime > mtimes[str(f)]:
                mtimes[str(f)] = mtime
                modified.add(f)
        if modified:
            return modified
        time.sleep(file_change_poll_interval_s)
        prev_files = cur_files
    raise ValueError(f"No template files found in {template_base}")

def load_context(template_path: Path) -> Mapping[str, Any]:
    """Load and validate context data from a context file.
    
    :param jfile:   The pathname of the JSON file to fetch context data from.
    
    :return:        The context as a map str:value.
    """
    context_file = template_path / 'context.json'
    if not context_file.exists() or not context_file.is_file():
        log.debug("No sample context found for %s. Place one at %s if you need one.", template_path, context_file)
        return {}
    try:
        jdict = json.loads(context_file.read_text(encoding='utf-8'))
    except ValueError as err:
        raise ValueError(f"Invalid content in context file {context_file}: {err}") from err
    if not isinstance(jdict, dict) or not all(isinstance(k, str) for k in jdict):
        raise ValueError(f"Context data in file '{context_file}' is malformatted: not an object mapping strings to values. Ignoring.")
    jdict = replace_time_values(jdict)
    log.debug("Successfully loaded context from %s: %s", context_file, jdict)
    return jdict

def store_config(confdir: Path, varname: str, varval: str, private=False) -> None:
    """Store a configuration item into the confdir.
    
    :param confdir:     Configuration directory in envdir style, holding one file per config key, with the file content holding the config value.
    :param varname:     Name of the config variable to store.
    :param varval:      Value of the config variable to store.
    :param private:     Make this setting inaccessible to other users.
    """
    if varval is None:
        return
    p = confdir / varname
    p.touch()
    if private:
        os.chmod(str(p), stat.S_IREAD | stat.S_IWRITE)
        p.write_bytes(obfuscate(varval, key='tattler_livepreview'))
    else:
        p.write_text(varval)
    setenv(varname, varval)

def load_stored_config(confdir: Path, varname: str, private: bool=False) -> str:
    """Return a previously-configured value for a variable, if any.
    
    :param confdir:     Path to the directory holding any previous configuration.
    :param varname:     The variable name to look up.
    :param private:     Whether the value is expected to be stored securely.
    :return:            The value of the variable stored, of None if not available.
    """
    existing_conf: Path = confdir / varname
    if not existing_conf.exists():
        return None
    if private:
        rawval = existing_conf.read_bytes()
        return unobfuscate(rawval, key='tattler_livepreview') or None
    return existing_conf.read_text().strip() or None

def load_config(confdir: Path) -> None:
    """Collect configuration data from user or previous envdir, and store it into the confdir.
    
    :param confdir:     Path to the directory holding any previous configuration.
    """
    gmail_srvaddr = 'smtp.gmail.com:465'
    confdir.mkdir(parents=True, exist_ok=True)
    for varname, help_text, default, private in [
        # varname, prompt_msg, default_value, is_private
        ('EMAIL', "To which email address to send live notifications?", None, False),
        ('TATTLER_EMAIL_SENDER', "From which email address? Type Enter if you don't care.", None, False),
        ('TATTLER_SMTP_ADDRESS', "What SMTP server to send through? Enter 'host:port', or 'gmail' to use gmail with your google account.", "localhost:25", False),
        ('TATTLER_SMTP_AUTH', "Any credentials needed for SMTP authentication? Your input is hidden and stored in a hard-to-decode format (Format: 'user:password').", None, True),
        ]:
        msg = ""
        conf[varname] = load_stored_config(confdir, varname, private)
        if varname == 'TATTLER_SMTP_AUTH' and conf['TATTLER_SMTP_ADDRESS'] == gmail_srvaddr:
            msg = "If your google account requires 2-factor authentication, Google requires an App Password to access SMTP. Get it @ https://myaccount.google.com/apppasswords and use it in place of your actual password. Enter your gmail credentials including domain (e.g. 'michael.jackson@gmail.com:MyPassword')"
        elif conf[varname]:
            varname_display = conf[varname]
            if private:
                varname_display = f'[*hidden*, {len(conf[varname])} characters]'
            msg = f"Type value or Enter to use previous setting = {varname_display}"
        else:
            msg = f"Default = {default}"
            conf[varname] = default
        prompt = f"\n\n==> {help_text}\n\n{msg} -> "
        userinput = get_user_input(prompt, private).strip()
        if varname == 'TATTLER_SMTP_ADDRESS' and userinput.lower() == 'gmail':
            userinput = gmail_srvaddr
        if userinput:
            conf[varname] = userinput
        store_config(confdir, varname, conf[varname], private)

def monitor_fire(template_base: Path):
    """Monitor files within template base and fire notification when one changes"""
    changed = files_changed(template_base)
    log.info("==> %s Files changed:\n%s", len(changed), '\n'.join(sorted(f"- {f}" for f in changed)))
    events_changed = {get_event_coordinates(changed_file) for changed_file in changed}
    for event_name, scope_name in events_changed:
        log.info("Event template '%s' changed on %s . Firing notification to %s.", event_name, datetime.now(), conf['EMAIL'])
        tpath = template_base / scope_name
        try:
            ctx = load_context(tpath / event_name)
        except ValueError as err:
            log.error("Error loading context for %s, skipping notification. Error was: %s", event_name, err)
            continue
        try:
            send_notification('email', event_name, [conf['EMAIL']], ctx, template_processor=get_template_processor(), template_base=tpath)
            log.info("Delivered successfully.")
        except jinja2.exceptions.UndefinedError as err:
            errmsg = str(err)
            if 'base_template' in str(err):
                errmsg = "Failed to load template: base is missing. Did you provide a '_base' template within your scope? See https://docs.tattler.dev/templatedesigners/base_templates.html"
            log.error("Failed to load template: %s", errmsg)
        except jinja2.exceptions.TemplateAssertionError as err:
            log.error("Failed to load template: %s", err)
    return changed

def get_conf_path(create: bool=False) -> Path:
    """Return the path where to store configuration, excised for mocking."""
    confpath = Path(tempfile.gettempdir()) / 'tattler_livepreview'
    if create:
        confpath.mkdir(exist_ok=True)
    return confpath

def usage() -> None:
    """Print usage instructions"""
    print("Usage:", file=sys.stderr)
    print("tattler_livepreview /path/to/template_dir", file=sys.stderr)

def check_templates_sanity(tbase: Path):
    """Validate that the path provided is holds scopes and events."""
    if not tbase.is_dir():
        raise FileNotFoundError(f"Templates path '{tbase}' is not a directory")
    scopes = get_scopes(tbase)
    email_events = set()
    for scope in scopes:
        tman = TemplateMgr(tbase / scope)
        tman.validate_templates()
        email_events |= {evname for evname in tman.available_events() if 'email' in tman.available_vectors(evname)}
    if not email_events:
        raise ValueError(f"No event with an email template found in template base {tbase}. livepreview only operates with email. Nothing to do here.")

def get_cmdline_args():                 # pragma: no cover
    """Wrap sys.argv for mocking"""
    return sys.argv

def main():
    """Entry point function for command line execution."""
    args = get_cmdline_args()
    if len(args) < 2:
        usage()
        return 1
    template_base = Path(args[1])
    try:
        check_templates_sanity(template_base)
    except (FileNotFoundError, ValueError) as err:
        log.error("Path '%s' is not a valid template base: %s", template_base, err)
        return 1
    conf_envdir = get_conf_path(create=True)
    store_config(conf_envdir, 'TATTLER_TEMPLATE_BASE', str(template_base))
    load_config(conf_envdir)
    log.info("\n==> Configured successfully. Configuration held in %s", conf_envdir)
    while True:
        try:
            monitor_fire(template_base)
        except FileNotFoundError as err:
            log.error("File does not exist: %s", err)
            return 1
        except ValueError as err:
            log.error("Value error: %s. Giving up.", err)
            return 1
        except KeyboardInterrupt:
            break
    return 0
