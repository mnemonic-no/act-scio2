"""
Helper functions for retrieving vocabulary aliases
"""

import argparse
import re
from typing import Any, Dict, List, Optional, Tuple

import requests
import urllib3  # type: ignore

ESCAPE_CHARS = [",", ":", "#"]


def unescape(s: str) -> str:
    """
    Unescape
    """

    for char in ESCAPE_CHARS:
        s = s.replace("\\{}".format(char), char)

    return s


def escape(s: str) -> str:
    """
    Escape
    """
    for char in ESCAPE_CHARS:
        s = s.replace(char, "\\{}".format(char))

    return s


class UnknownResult(Exception):
    """UnknownResult is used in API request (not 200 result)"""

    def __init__(self, *args: Any, **kwargs: Dict[Any, Any]) -> None:
        Exception.__init__(self, *args, **kwargs)


def parse_aliases(line: str) -> Tuple[str, List[str]]:
    """
    Parse line on this form:

    name:alias1, alias2, alias3

    Supports escaping of ":", "," and "#"

    returns:
    name and list of aliases
    """

    # Split on ":" unless they are escaped
    vocab, aliases_str = re.split(r'(?<!\\):', line, maxsplit=1)

    # Split aliases on ",", unless they are escaped
    aliases = [unescape(a.strip())
               for a in re.split(r'(?<!\\),', aliases_str)
               if a.strip()]

    return unescape(vocab.strip()), aliases


def parseargs() -> argparse.ArgumentParser:
    """ Parse arguments """
    parser = argparse.ArgumentParser(description="Fetch ISO 3166 data")
    parser.add_argument('--http-timeout', dest='timeout', type=int,
                        default=120, help="Timeout")
    parser.add_argument(
        '--proxy-string',
        dest='proxy_string',
        help="Proxy to use for external queries")
    parser.add_argument(
        '--data-dir',
        dest='data_dir',
        required=True,
        help="Output path for data")

    return parser


def output_alias(filename: str, alias_map: Dict, exclude: Optional[List] = None) -> None:
    """
    Output alias to file
    """
    if not exclude:
        exclude = []

    with open(filename, "w") as f:
        for key in sorted(alias_map.keys()):
            aliases = alias_map[key]
            aliases = [escape(alias).strip() for alias in sorted(aliases)
                       if alias not in exclude and alias != key]
            f.write("{}:{}\n".format(escape(key).strip(), ",".join(aliases)))


def merge(*lists: Dict, lower: bool = False) -> Dict:
    """
    Combine multiple alias lists in order.
    If key exists as one of the previous alias lists, add aliases to the previous
    main key
    """

    combined: Dict = {}

    for alias_list in lists:
        for key, aliases in alias_list.items():
            if lower:
                key = key.lower()
                aliases = [alias.lower() for alias in aliases]

            # One of our aliases is already main group name in ATT&CK.
            # Merge aliases from MISP (including "main" group name with ATT&CK)
            alias_in_keys = [alias for alias in aliases if combined.get(alias)]

            if alias_in_keys:
                key = alias_in_keys[0]

            combined[key] = list(set(combined.get(key, []) + aliases))

    return combined


def fetch_json(
        url: str,
        proxy_string: str = "",
        timeout: int = 60,
        verify_https: bool = True) -> Dict:
    """Fetch remote URL as JSON
    url (string):                    URL to fetch
    proxy_string (string, optional): Optional proxy string on format host:port
    timeout (int, optional):         Timeout value for query (default=60 seconds)
    """

    proxies = {
        'http': proxy_string,
        'https': proxy_string
    }

    options = {
        "verify": verify_https,
        "timeout": timeout,
        "proxies": proxies,
        "params": {}
    }

    if not verify_https:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Unable to infer type
    req = requests.get(url, **options)  # type: ignore

    if not req.status_code == 200:
        errmsg = "status_code: {0.status_code}: {0.content}"
        raise UnknownResult(errmsg.format(req))

    # Unable to infer type of json()
    return req.json()  # type: ignore
