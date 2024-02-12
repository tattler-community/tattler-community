import os
import sys
import logging

from tattler_py.tattler_client_http import TattlerClientHTTP
from tattler_py.serialization import deserialize_json

log = logging.getLogger(__name__)
log.setLevel(os.getenv('LOG_LEVEL', 'info').upper())

srv_addr, srv_port = '127.0.0.1', 11503

def get_deadletters_path():
    dlpath = os.getenv("TATTLER_DEADLETTER_PATH")
    if dlpath and os.path.exists(dlpath):
        return dlpath
    if len(sys.argv) > 1:
        dlpath = sys.argv[1]
        if os.path.exists(dlpath):
            return dlpath
    return '.'

def get_deadletters(path=None):
    def get_dl_files(p):
        return sorted(filter(lambda fn: fn.endswith('.txt') and len(fn.split('_')) == 5, os.listdir(p)))
    # search in argument
    if dlpath is None:
        dlpath = get_deadletters_path()
    try:
        return get_dl_files(dlpath)
    except OSError as e:
        log.error(f"Error opening deadletter path {dlpath} (from envvar TATTLER_DEADLETTER_PATH or first argument or .): {e}")

def parse_deadletter(fname):
    # scope, rcpt, event, pid, timestamp = fname.split('_')
    # rcpt = int(rcpt)
    return deserialize_json(open(fname).read())

def remove_deadletter(fname):
    dlpath = get_deadletters_path()
    filename = os.path.join(dlpath, fname)
    os.remove(filename)

def deliver_deadletters(dls):
    for dl in dls:
        dlinfo = parse_deadletter(dl)
        ntf = TattlerClientHTTP(dlinfo['scope'], srv_addr, srv_port, mode='staging')
        try:
            res = ntf.send(dlinfo['vectors'], dlinfo['event'], int(dlinfo['recipient']), context=dlinfo['definition'], priority=dlinfo['priority'], correlationId=dlinfo['correlationId'])
        except:
            log.exception(f"Error sending {dl} (skipping and continuing):")
        else:
            if res:
                log.info(f"Notification '{dl}' sent successfully. Removing")
                remove_deadletter(dl)

def main():
    dlfilenames = get_deadletters()
    input(f"Found {len(dlfilenames)} dead letters. Continue with actual delivery? (Ctrl-C to cancel)")
    deliver_deadletters(dlfilenames)

if __name__ == '__main__':
    main()