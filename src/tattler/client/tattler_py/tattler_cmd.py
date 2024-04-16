"""Command-line interface to tattler client"""

import re
import argparse
import logging
import os
import sys
import json
from typing import Tuple

from tattler.client.tattler_py import send_notification

log = logging.getLogger(__name__)
log.setLevel(os.getenv('LOG_LEVEL', 'info').upper())

def alnum_argument(value: str) -> str:
    """Validate that a parameter is alphanumeric with . _ -"""
    if not re.match(r'^[a-zA-Z0-9._-]+$', value):
        raise argparse.ArgumentTypeError("must be alphanumeric with possibly {_, -, .} values")
    return value

def parse_cmdline(args):
    """Get operating parameters from command line"""
    def contextvar(val: str) -> Tuple[str, str]:
        if '=' not in val:
            raise ValueError("context variable must be formatted like 'name=value'")
        if val.startswith('='):
            raise ValueError("Some name must be given for context variable, i.e. 'name=value'")
        return val.split('=', 1)

    def server_endpoint_spec(val: str) -> Tuple[str, int]:
        srv = '127.0.0.1'
        port = 11503
        if val:
            srv = val
            if ':' in val:
                srv, port = val.rsplit(':')
                port = int(port)
        return srv, port

    parser = argparse.ArgumentParser(prog='tattler_notify', description='Send notifications through a tattler server')
    parser.add_argument('recipient', help='ID of recipient to notify')
    parser.add_argument('scope', help='name of scope holding event', type=alnum_argument)
    parser.add_argument('event_name', help='name of event to notify', type=alnum_argument)
    parser.add_argument('context', nargs='*', default={}, type=contextvar, help='Optional key=value variables to add to context. Repeat to set multiple variables. Default: no context.')
    parser.add_argument('-v', '--vectors', type=(lambda x: x.split(',')), help="Optional comma-separated list of vectors to restrict the notification to. Default: deliver to all event-defined vectors.")
    parser.add_argument('-s', '--server', type=server_endpoint_spec, default="127.0.0.1:11503", help="Optional address:port of tattler server to request notification to. Default: 127.0.0.1:11503.")
    parser.add_argument('-m', '--mode', choices={'debug', 'staging', 'production'}, default="debug", help="Optional mode for sending the notification (debug, staging, production). Default: debug.")
    parser.add_argument('-p', '--priority', type=int, choices={1, 2, 3, 4, 5}, help="Optional priority for the notification. Default: None.")
    parser.add_argument('-j', '--json-context', type=argparse.FileType('r', encoding='utf-8'), help='Optional path to a JSON file holding context data. Any command-line context vars gets merged on top of it.')
    return parser.parse_args(args=args)

def main():
    """Main function run on command line call."""
    args = parse_cmdline(sys.argv[1:])
    if args.json_context:
        jctx = json.load(args.json_context)
        if not isinstance(jctx, dict):
            raise ValueError(f"Context file must be a dictionary (JSON object), not {type(jctx)}")
        args.context = {**jctx, **dict(args.context)}
    success, details = send_notification(args.scope, args.event_name, args.recipient, dict(args.context), vectors=args.vectors, mode=args.mode, priority=args.priority, srv_addr=args.server[0], srv_port=args.server[1])
    if success:
        log.info("Notification succeeded. Details: %s", details)
    else:
        log.error("Notification failed. Details: %s", details)
        sys.exit(1)

if __name__ == '__main__':
    main()
