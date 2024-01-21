#! python

from typing import Iterable, Mapping, Tuple
from datetime import datetime, timedelta
import re
import logging
import sys
import urllib.request
import urllib.error
import time
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)

url_re = re.compile(r'''https?://[^"\s<>{}\)`\\']+''')

# store URL outcomes into this filename, or None to disable
cache_file = None
# map URL -> outcome for previously tested URLs
cached_urls = {}

# do not scan for links files whose pathname contains any of these literal strings
exclude_paths = ['/test', '/venv', '__pycache__', 'docs/build/', 'templates/', 'tattler.egg-info']

# ignore URLs that contain any of these literal strings; empty to exclude none
exclude_urls = ['127.0.0.1', 'api.bulksms.com/v1', 'pypi.tattler.dev', '/company.intranet']
# only consider URLs that contain any of these literal strings; empty to include all
# include_urls = ['tattler.dev', 'tattler.readthedocs.io']
include_urls = []

# do not attempt to open a URL for longer than these many seconds
HTTP_TIMEOUT = 5

def get_links(content: str, includes: Iterable[str]=None, excludes: Iterable[str]=None) -> Iterable[str]:
    """Return the list of links in a string"""
    includes = includes or []
    all_urls = url_re.findall(content)
    if excludes:
        all_urls = [u for u in all_urls if not any(rule in u for rule in excludes)]
    if includes:
        all_urls = [u for u in all_urls if any(rule in u for rule in excludes)]
    return all_urls

def get_file_links(rootpath: Path, excludes_path: Iterable[str]=None, include_urls: Iterable[str]=None) -> Mapping[str, Iterable[str]]:
    """Walk over all files in a path and return their links"""
    excludes_path = excludes_path or []
    file_links = {}
    for p in rootpath.rglob('*'):
        if any(rule in str(p) for rule in excludes_path):
            logging.debug("Ignoring file '%s' as it matches an excludes rule", str(p))
            continue
        if p.is_dir():
            continue
        logging.info("Scanning file %s", p)
        try:
            content = p.read_text(encoding='utf-8').strip()
        except UnicodeDecodeError:
            logging.debug("Ignoring binary file %s", p)
            continue
        if content:
            file_links[p] = get_links(content, includes=include_urls, excludes=exclude_urls)
    return file_links

def link_valid(link: str) -> bool:
    """Return whether a link is valid"""
    if link in cached_urls:
        return cached_urls[link][1]
    try:
        logging.info("Checking link %s ...", link)
        req = urllib.request.Request(
            link,
            data=None,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT):
            pass
    except urllib.error.URLError as err:
        if err.status == 429:
            logging.info("Link '%s' returns %s '%s' -> assuming valid", link, err.status, err.reason)
            result = True
        else:
            logging.debug("Link '%s' appears invalid: %s", link, err)
            result = False
    except TimeoutError:
        logging.warning("Link '%s' timed out. Assuming error is temporary and link is valid.", link)
        result = True
    else:
        result = True
    cached_urls[link] = int(time.time()), result
    logging.info("%s valid? %s", link, result)
    return result

def find_files_with_invalid_links(file_links: Mapping[Path, Iterable[str]]) -> Mapping[Path, Iterable[str]]:
    """Return files that contain invalid links"""
    files_invalid_links = {}
    for fpath, flinks in file_links.items():
        for link in flinks:
            if not link_valid(link):
                if fpath not in files_invalid_links:
                    files_invalid_links[fpath] = set()
                files_invalid_links[fpath].add(link)
    return files_invalid_links

def display_invalid(file_links: Mapping[str, Iterable[str]]):
    for fname, links in file_links.items():
        logging.warning("%s", fname)
        for link in links:
            logging.warning("\t%s", link)

def load_url_cache(fname: Path) -> Mapping[str, bool]:
    """Load URL test results from a filename"""
    def outdated(tstamp: float) -> bool:
        return datetime.now() - datetime.fromtimestamp(tstamp) > timedelta(days=3)
    cache = {}
    if fname.is_file():
        content = fname.read_text(encoding='utf-8')
        for line in content.splitlines():
            result, tstamp, url = line.strip().split(',', 2)
            if not outdated(float(tstamp)):
                cache[url] = [tstamp, (result == '1')]
    return cache

def update_url_cache(fname: Path, values: Mapping[str, Tuple[float, bool]]):
    logging.debug("Updating cache -> %s ...", fname)
    with open(fname, mode='w+', encoding='utf-8') as f:
        for url, v in values.items():
            tstamp = v[0]
            res = '1' if v[1] else '0'
            line = ','.join([str(res), str(tstamp), url])
            f.write(line + '\n')
    logging.info("Updated cache %s with %s entries ...", fname, len(values))


def main():
    """Run main code"""
    global cached_urls
    global cache_file
    try:
        src = Path(sys.argv[1])
    except IndexError:
        src = Path(__file__).parent
    try:
        cache_file = Path(sys.argv[2])
        cached_urls = load_url_cache(cache_file)
    except IndexError:
        cache_file = None
    # src = Path(__file__).parent.parent.joinpath('package', 'src', 'tattler')
    # cache_file = Path('urlcache.csv')
    if cached_urls:
        logging.info("Loaded URL cache with %s entries", cached_urls)
    logging.info("Scanning files for links in '%s' ...", src)
    file_links = get_file_links(src, excludes_path=exclude_paths, include_urls=include_urls)
    logging.info("Scanning done. Now validating links ...")
    finv = find_files_with_invalid_links(file_links)
    finv = {str(n): v for n, v in finv.items()}
    if cache_file:
        update_url_cache(cache_file, cached_urls)
    if finv:
        logging.warning("Invalid links:")
        display_invalid(finv)
        sys.exit(1)
    else:
        logging.info("All good in %d files and %s", len(file_links), file_links.values())

if __name__ == '__main__':
    main()
