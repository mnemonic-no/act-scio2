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

from typing import Dict

import logging
import urllib3


from act.scio.feeds import conf, download

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGGER = logging.getLogger('root')


def main() -> None:
    """Main program loop. entry point"""
    args = conf.get_args()
    logformat = '%(asctime)-15s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s'  # NOQA

    logcfg: Dict = {
        "format": logformat,
        "level": logging.WARN,
    }

    if args.verbose:
        logcfg['level'] = logging.INFO

    if args.debug:
        logcfg['level'] = logging.DEBUG

    if args.log:
        logcfg['filename'] = args.log

    logging.basicConfig(**logcfg)
    try:
        full_feeds, partial_feeds = conf.parse_feed_file(args.feeds)
        download.download_feed_list(args, full_feeds, download.handle_feed, partial=False)
        download.download_feed_list(args, partial_feeds, download.handle_feed, partial=True)
    except IOError as err:
        LOGGER.error(str(err))
        raise err


if __name__ == "__main__":
    main()
