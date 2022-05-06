#!/usr/bin/env python3
"""Copyright 2019,2020 mnemonic AS <opensource@mnemonic.no>

Permission to use, copy, modify, and/or distribute this software for
any purpose with or without fee is hereby granted, provided that the
above copyright notice and this permission notice appear in all
copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

---
Download feeds from the feeds.txt file, store feed content in .html and feed
metadata in .meta files. Also attempts to download links to certain document
types"""

import datetime
import hashlib
import logging
import os
from typing import Dict, List, Text

import urllib3

from act.scio.config import get_cache_dir
from act.scio.feeds import cache, conf, download, upload
from act.scio.logsetup import setup_logging
from act.scio.tlp import valid_tlp

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # type: ignore


def sha256_of_file(filename: Text) -> Text:
    """Compute sha256 hexdigest of file"""

    with open(filename, "rb") as f:
        data = f.read()
        return hashlib.sha256(data).hexdigest()


def upload_uncached_files(
    cache_file: Text, files: List[Dict[Text, Text]], scio_url: Text, tlp: Text
) -> int:
    """Check each downloaded file hexdigest against a cache of previously uploaded
    files. Only upload "new" files."""

    mycache = cache.Cache(cache_file)

    nup = 0

    for filemap in files:

        filename: Text = filemap["filename"]
        sha256 = sha256_of_file(filename)

        if not mycache.contains(sha256):
            try:
                if scio_url != "dummy.url":
                    upload.upload(scio_url, filemap, tlp)
                mycache.insert(filename, sha256, str(datetime.datetime.now()))
                logging.info("Uploaded %s to scio", filename)
                nup += 1
            except upload.UploadError as err:
                logging.error(err)

    return nup


def main() -> None:
    """Main program loop. entry point"""

    args = conf.get_args()

    if args.tlp:
        args.tlp = args.tlp.upper()

        if not valid_tlp(args.tlp):
            logging.error(f"Illegal TLP: {args.tlp}")
            return

    if not args.store_path:
        args.store_path = get_cache_dir("scio-feeds", create=True)

    p = os.path.join(args.store_path, "download")
    if not os.path.isdir(p):
        os.makedirs(p)

    setup_logging(args.loglevel, args.logfile, "scio-feed-download")

    files: List[Dict[Text, Text]] = []

    try:
        full_feeds, partial_feeds = conf.parse_feed_file(args.feeds)
        files += download.download_feed_list(args, full_feeds, partial=False)
        files += download.download_feed_list(args, partial_feeds, partial=True)
    except IOError as err:
        logging.error(str(err))
        raise err

    if not args.scio:
        logging.info("No Scio API Url provided. Exit after download[%s]", len(files))
        return

    logging.info("Checking upload status of %s files", len(files))

    nup = upload_uncached_files(args.cache, files, args.scio, args.tlp)

    logging.info("Uploaded %s files", nup)


if __name__ == "__main__":
    main()
