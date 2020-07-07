"""Helper function related to feed configuration"""

from enum import Enum
from typing import Text, Optional, Tuple, List
import argparse
import caep
import logging
import os

from act.scio.config import get_cache_dir

FeedType = Enum('FeedType', ['none', 'partial', 'full'])

def get_args() -> argparse.Namespace:
    """initialize argument parser"""

    parser = argparse.ArgumentParser(description="pull feeds into html files")
    parser.add_argument("-l", "--log", type=str,
                        help="Which file to log to (default: stdout)")
    parser.add_argument("--file-format", nargs="+", default="pdf doc xls csv xml")
    parser.add_argument(
        "--store-path",
        help="Location for stored files. Default = ~/.cache/scio-feeds (honors $XDG_CACHE_HOME")
    parser.add_argument("-v", "--verbose", action="store_true", help="Log level DEBUG")
    parser.add_argument("--debug", action="store_true", help="Log level DEBUG")
    parser.add_argument("--ignore", type=str, help="file with ignore patterns")
    parser.add_argument("--feeds", default="feeds.txt", type=str,
                        help="feed urls (one pr. line) (default: feeds.txt)")
    parser.add_argument("--cache", default="cache.db", help="sqlite db containing cached hashes")
    parser.add_argument("--scio", default=None, help="Upload to scio engine API url")
    parser.add_argument('--logfile')
    parser.add_argument('--loglevel', default="info")

    args: argparse.Namespace = caep.config.handle_args(parser, "scio/etc", "scio", "feed")

    if not args.store_path:
        args.store_path = get_cache_dir("scio-feeds", create=True)

    p = os.path.join(args.store_path, "download")
    if not os.path.isdir(p):
        os.makedirs(p)

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

    for linenum, feed_line in enumerate(open(filename)):
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
