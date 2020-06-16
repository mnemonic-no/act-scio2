#!/usr/bin/env python3

"""Copyright 2019 mnemonic AS <opensource@mnemonic.no>

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
Program to check the feed output directory of feed_downloader.py
Any downloaded content not found in the cache is handled.
The .meta files associated with the .html files from the feed download is
kept to preserve information about source and original titles as well as
feed time and date stamps.
This files builds a document understood by SCIOs 'doc' work queue.
This utility is not meant to handle the files downloaded from links _in_ the
feed as these document does not share any of the meta-data associated with
the feed entries. These files need to be handled separately (using SCIOs own
submit utility.
"""

import logging
import sys
from typing import Optional, Text
from logging.handlers import RotatingFileHandler


def setup_logging(
        loglevel: Text = "debug",
        logfile: Optional[Text] = None,
        prefix: Text = "scio",
        maxBytes: int = 100000000,  # 100 MB
        backupCount: int = 6):
    """ Setup loglevel and optional log to file """
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)

    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = "[%(asctime)s] app=" + prefix + " level=%(levelname)s msg=%(message)s"

    if logfile:
        handlers = [
            RotatingFileHandler(
                logfile,
                maxBytes=maxBytes,
                backupCount=backupCount)]

        logging.basicConfig(
            level=numeric_level,
            handlers=handlers,
            format=formatter,
            datefmt=datefmt)
    else:
        logging.basicConfig(
            level=numeric_level,
            stream=sys.stdout,
            format=formatter,
            datefmt=datefmt)
