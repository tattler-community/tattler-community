import os
import sys
import logging
from typing import Iterable, Any, Mapping, Optional

from tattler.utils.serialization import deserialize_json
from tattler_py.tattler_client_http import TattlerClientHTTP

log = logging.getLogger(__name__)
log.setLevel(os.getenv('LOG_LEVEL', 'info').upper())

srv_addr, srv_port = '127.0.0.1', 11503

def get_deadletters_path() -> str:
    """Return the configured path of deadletters.
    
    :return:    Pathname of directory holding deadletters.
    """
    dlpath = os.getenv("TATTLER_DEADLETTER_PATH")
    if dlpath and os.path.exists(dlpath):
        return dlpath
    if len(sys.argv) > 1:
        dlpath = sys.argv[1]
        if os.path.exists(dlpath):
            return dlpath
    return '.'

def get_deadletters(dlpath: Optional[str]=None) -> Iterable[str]:
    """Return the list of available deadletters.
    
    :param dlpath:  Search in directory with this path instead of configured deadletter path.

    :return:    Iterable with valid deadletter filenames, or empty upon error (e.g. path not accessible).
    """
    if dlpath is None:
        dlpath = get_deadletters_path()
    try:
        # extract files named with deadletter format
        return sorted(fn for fn in os.listdir(dlpath) if fn.endswith('.json') and len(fn.split('_')) == 5)
    except OSError as e:
        log.error("Error opening deadletter path %s (from envvar TATTLER_DEADLETTER_PATH or first argument or .): %s", dlpath, e)
        return []

def parse_deadletter(fname: str) -> Mapping[str, Any]:
    """Parse the content of a deadletter file.
    
    :param fname:   Path of file holding one deadletter.

    :return:        A mapping with keys {'vectors': [], 'event': str, 'recipient': str, 'context': str, 'priority': bool, 'correlationId': str}
    """
    with open(fname, encoding='utf-8') as f:
        return deserialize_json(f.read())

def remove_deadletter(fname: str) -> None:
    """Clear a deadletter file from filesystem.
    
    :param fname:   Filename to remove, to be found in deadletter path."""
    dlpath = get_deadletters_path()
    filename = os.path.join(dlpath, fname)
    os.remove(filename)

def deliver_deadletters(dls: Iterable[str]) -> None:
    """Iterate through a list of deadletter files and deliver each.
    
    :param dls:     Iterable of deadletter filenames"""
    for dl in dls:
        dlinfo = parse_deadletter(dl)
        ntf = TattlerClientHTTP(dlinfo['scope'], srv_addr, srv_port, mode='staging')
        try:
            res = ntf.send(dlinfo['vectors'], dlinfo['event'], int(dlinfo['recipient']), context=dlinfo['definition'], priority=dlinfo['priority'], correlationId=dlinfo['correlationId'])
        except:
            log.exception("Error sending %s (skipping and continuing):", dl)
        else:
            if res:
                log.info("Notification '%s' sent successfully. Removing", dl)
                remove_deadletter(dl)

def main():
    """First code to execute when running in script mode"""
    dlfilenames = get_deadletters()
    input(f"Found {len(dlfilenames)} dead letters. Continue with actual delivery? (Ctrl-C to cancel)")
    deliver_deadletters(dlfilenames)

if __name__ == '__main__':
    main()