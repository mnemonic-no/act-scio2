"""Helper function related to feed configuration"""

import os
from enum import Enum
from typing import Text, Optional, Tuple, List
import argparse
import caep
import logging


FeedType = Enum('FeedType', ['none', 'partial', 'full'])

XDG_CONFIG = os.path.expanduser(os.environ.get("XDG_CONFIG_HOME", "~/.config"))
XDG_CACHE = os.path.expanduser(os.environ.get("XDG_CACHE_HOME", "~/.cache"))

def get_args() -> argparse.Namespace:
    """initialize argument parser"""

    parser = argparse.ArgumentParser(description="pull feeds into html files")
    parser.add_argument("-l", "--log", type=str,
                        help="Which file to log to (default: stdout)")
    parser.add_argument("--file-format", nargs="+", default="pdf doc xls csv xml")
    parser.add_argument(
        "--store-path",
        help=f"Location for stored files. Default {XDG_CACHE}/scio-feeds")
    parser.add_argument('--proxy-string', help="Proxy to use for external queries")
    parser.add_argument("--ignore", type=str, help="file with ignore patterns")
    parser.add_argument("--feeds", default=caep.get_config_dir("scio/etc/feeds.txt"),
                        type=str, help=f"feed urls (one pr. line). Default: {XDG_CONFIG}/scio/etc/feeds.txt")
    parser.add_argument("--cache", default=caep.get_cache_dir("scio-feeds/cache.db"),
                        help=f"sqlite db containing cached hashes. Default = {XDG_CACHE}/scio-feeds/cache.db")
    parser.add_argument("--scio", help="Upload to scio engine API url. " +
                        "Set to empty value to not upload files.",
                        default="http://localhost:3000/submit")
    parser.add_argument("--stoplist", default=caep.get_config_dir("scio/etc/secstoplist.txt"),
                        help="Provided own stoplist for text extraction")
    parser.add_argument('--logfile')
    parser.add_argument('--loglevel', default="info")

    args: argparse.Namespace = caep.config.handle_args(parser, "scio/etc", "scio.ini", "feeds")

    return args


def get_feed_url_from_feed_file_line(line: Text) -> Optional[Text]:
    """Extract the url portion from the feed file line"""

    if len(line) <= 2:
        logging.warning("Missconfigured feed file line: %s", line)
        return None

    feed_url = line[2:].strip()
    if not feed_url:
        logging.warning("Empty URL part of feed file line: %s", line)

    return feed_url


def get_feed_kind(line: Text) -> FeedType:
    """Extract the feed kind from a feed config line"""

    if len(line) < 2:
        return FeedType.none
    type_text = line[:2]
    if type_text == 'p ':
        return FeedType.partial
    if type_text == 'f ':
        return FeedType.full

    return FeedType.none


def parse_feed_file(filename: Text) -> Tuple[List[Text], List[Text]]:
    """Parse feed file, split feeds into partial and full feeds
    (lines starting with 'f ' and 'p ')"""

    full_feeds = []
    partial_feeds = []

    for linenum, feed_line in enumerate(open(os.path.expanduser(filename))):
        feed_type = get_feed_kind(feed_line)
        feed_url = get_feed_url_from_feed_file_line(feed_line)
        if not feed_url:
            continue

        if feed_type == FeedType.none:
            logging.error("Unable to parse line %s [%s]", linenum + 1, feed_line)
            continue

        if feed_type == FeedType.full:
            full_feeds.append(feed_url)
        if feed_type == FeedType.partial:
            partial_feeds.append(feed_url)

    return full_feeds, partial_feeds
