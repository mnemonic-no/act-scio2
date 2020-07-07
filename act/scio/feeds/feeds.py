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

from typing import Dict, List, Text

import datetime
import hashlib
import logging
import urllib3

from act.scio.feeds import conf, download, cache, upload
from act.scio.logging import setup_logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main() -> None:
    """Main program loop. entry point"""

    args = conf.get_args()
    logformat = '%(asctime)-15s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s'  # NOQA

    setup_logging(args.loglevel, args.logfile, "scio-feed-download")

    files: List[Text] = []
    try:
        full_feeds, partial_feeds = conf.parse_feed_file(args.feeds)
        files += download.download_feed_list(args, full_feeds, partial=False)
        files += download.download_feed_list(args, partial_feeds, partial=True)
    except IOError as err:
        logging.error(str(err))
        raise err

    mycache = cache.Cache(args.cache)

    if not args.scio:
        logging.info("No Scio API Url provided. Exit after download[%s]", len(files))
        return

    logging.info("Checking upload status of %s files", len(files))

    nup = 0
    for filename in files:

        if not filename.strip():
            continue  # skip "blank" filenames

        with open(filename, "rb") as f:
            data = f.read()
            sha256 = hashlib.sha256(data).hexdigest()
            if not mycache.contains(sha256):
                try:
                    upload.upload(args.scio, filename)
                    mycache.insert(filename, sha256, str(datetime.datetime.now()))
                    logging.info("Uploaded %s to scio", filename)
                    nup += 1
                except upload.UploadError as err:
                    logging.error(err)

    logging.info("Uploaded %s files", nup)


if __name__ == "__main__":
    main()
