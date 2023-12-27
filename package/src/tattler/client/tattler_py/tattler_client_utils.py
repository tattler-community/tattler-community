import os
import re
import random
import string

DEFAULT_ADDRESS = '127.0.0.1'
DEFAULT_PORT = 11503

def get_server_endpoint(envvar_name='TATTLER_SERVER'):
    """Retrieve the endpoint parameters for the server from the environment."""
    endpoint = os.getenv(envvar_name)
    if not endpoint:
        raise RuntimeError(f"No endpoint set: missing or empty '{envvar_name}' envvar.")
    # IPv4
    addrport_match = re.match(r'^((?P<address>(?P<address_ip6>\[.*\])|(?P<address_ip4>(\d+\.){3}(\d+))))?(:(?P<port>\d+))?$', endpoint)
    if not addrport_match:
        raise RuntimeError(f"Given endpoint '{endpoint}' from envvar '{envvar_name}' does not match format '[ip6]:port' or 'ip4:port' or '[ip6]' or 'ip4'.")
    if addrport_match.group('address_ip6'):
        addr = addrport_match.group('address_ip6')[1:-1]
    elif addrport_match.group('address_ip4'):
        addr = addrport_match.group('address_ip4')
    else:
        addr = DEFAULT_ADDRESS

    return addr, int(addrport_match.group('port') or DEFAULT_PORT)

def mk_correlation_id(len_=10, prefix=None):
    """Return a random string as unique identifier.
    
    @param len_     [int]       Length of random characters (up to 40).
    @param prefix   [str]       An optional prefix to add to the string.
    @return         [str]       A random identifier of the requested length."""
    s = ''.join(random.choices(string.ascii_lowercase + string.digits, k=len_))
    if prefix:
        return f"{prefix}:{s}"
    return s
