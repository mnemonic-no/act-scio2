#!/usr/bin/env python3

import argparse
import base64
import hashlib
import os.path
import sys
from typing import Any, Dict, Optional, Text, Tuple

import requests

from act.scio import tlp
from act.scio.models import Document

"Submit content of URI / File to SCIO"


def fatal(message: Text, exit_code: int = 1) -> None:
    "Print error message and abort"
    sys.stderr.write(message + "\n")
    sys.exit(exit_code)


VALID_TLP = ", ".join(tlp.TLP_ALLOWED_VALUES)


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    + "Chrome/112.0.0.0 Safari/537.36"
)


def parseargs(description: Text) -> argparse.Namespace:
    """Parse arguments"""
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("--http-timeout", type=int, default=120, help="Timeout")
    parser.add_argument("--proxy-string", help="Proxy to use for external queries")
    parser.add_argument("--scio-baseuri", required=True, help="SCIO API URI")
    parser.add_argument("--http-user", help="SCIO HTTP Basic Auth user")
    parser.add_argument(
        "--http-user-agent",
        default=DEFAULT_USER_AGENT,
        help="User agent used to download from uri",
    )
    parser.add_argument("--http-password", help="SCIO HTTP Basic Auth password")
    parser.add_argument("--uri", help="Download content from URI and submit content")
    parser.add_argument("--filename", help="Submit file")
    parser.add_argument(
        "--nostore",
        action="store_true",
        help="Do not store document to elasticsearch/disk",
    )
    parser.add_argument("--tlp", default="AMBER", help=f"tlp ({VALID_TLP})")
    parser.add_argument("--owner", help="Document owner (identifier)")
    args = parser.parse_args()

    if not (args.uri or args.filename):
        fatal("Specify either --uri or --filename")

    args.tlp = args.tlp.upper()

    if not tlp.valid_tlp(args.tlp):
        fatal(f"Invalid TLP: {args.tlp}. Must be one of: {VALID_TLP}")

    return args


def get_uri(
    uri: Text,
    proxies: Optional[Dict[Text, Any]],
    timeout: Optional[int] = 30,
    user_agent: Optional[str] = None,
) -> bytes:
    "Return content from URI"

    headers = {"User-Agent": user_agent} if user_agent else {}

    req = requests.get(uri, proxies=proxies, timeout=timeout, headers=headers)

    if not req.status_code == 200:
        fatal("Unable to get {}. Status code={}".format(uri, req.status_code))

    return req.content


def get_file(filename: Text) -> bytes:
    "Return content from file"
    with open(filename, "rb") as f:
        return f.read()


def scio_submit(
    submit_uri: Text,
    content: bytes,
    filename: Text,
    owner: Optional[Text],
    auth: Optional[Tuple[Text, Text]],
    uri: Optional[Text],
    tlp: tlp.TLP = "AMBER",
    store: bool = False,
) -> None:
    "Submit content with specified filename to SCIO"

    sha256 = hashlib.sha256(content).hexdigest()

    # If filename is not specified, use sha256
    if not filename:
        filename = sha256

    document = Document(
        content=base64.b64encode(content).decode("utf8"),
        tlp=tlp,
        filename=filename,
        owner=owner,
        store=store,
        uri=uri,
    )

    req = requests.post(submit_uri, json=document.dict(), auth=auth)

    if not req.status_code == 200:
        fatal(f"Unable to submit {filename} to scio ({submit_uri}), error={req.text}")

    print(f"Submitted {sha256}: {req.text}")


def main() -> None:
    "main function"

    args = parseargs("SCIO submit from URI/File")
    auth = (args.http_user, args.http_password) if args.http_user else None

    proxies = (
        {"http": args.proxy_string, "https": args.proxy_string}
        if args.proxy_string
        else None
    )

    if args.uri:
        content = get_uri(
            args.uri,
            proxies=proxies,
            timeout=args.http_timeout,
            user_agent=args.http_user_agent,
        )
        # Use basename from URI as filename
        filename = os.path.basename(args.uri)

    elif args.filename:
        content = get_file(args.filename)
        # Use basename from file
        filename = os.path.basename(args.filename)

    try:
        scio_submit(
            args.scio_baseuri,
            content,
            filename,
            args.owner,
            auth,
            args.uri if args.uri else None,
            args.tlp,
            not args.nostore,
        )
    except requests.exceptions.ConnectionError as e:
        fatal(f"Unable to connect to {args.scio_baseuri}: {e}")


if __name__ == "__main__":
    main()
