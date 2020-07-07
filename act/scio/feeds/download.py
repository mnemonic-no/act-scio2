"""Helper functions related to downloading feeds and files"""

from typing import Text, Optional, Any, Dict, cast, List, Tuple
import argparse
import concurrent.futures
import logging
import os.path
import requests
import shutil
import urllib.parse

import feedparser

from act.scio.feeds import analyze, extract


def download_and_store(
        feed_url: Text,
        ignore_file: Optional[Text],
        storage_path: Text,
        link: Text) -> Text:
    """Download and store a link. Storage defined in args"""

    # check if the actual url is in the ignore file. If so, no download will take place.
    if analyze.in_ignore_file(link, ignore_file):
        logging.info("Download link [%s] in ignore file.", link)
        return ""

    logging.info("downloading %s", link)

    parsed_link = analyze.parse_and_correct_link(link)

    # if netloc does not contain a hostname, assume a relative path to the feed url
    if parsed_link.netloc == '':
        parsed_feed_url = urllib.parse.urlparse(feed_url)
        parsed_link = parsed_link._replace(scheme=parsed_feed_url.scheme,
                                           netloc=parsed_feed_url.netloc,
                                           path=parsed_link.path)
        logging.info("possible relative path %s, trying to append host: %s",
                     parsed_link.path, parsed_feed_url.netloc)

    req = requests.get(parsed_link.geturl(),
                       headers=default_headers(),
                       verify=False,
                       stream=True,
                       timeout=60)

    if req.status_code >= 400:
        logging.info("Status %s - %s", req.status_code, link)
        return ""

    fname = os.path.join(storage_path,
                         "download",
                         extract.safe_filename(os.path.basename(parsed_link.path)))

    # check if the filename on disk is in the ignore file. If so, do not return filename
    # for upload. This differ from URL in the ignore file as the file is in fact downloaded by
    # the feed worker, but not uploaded to Scio.
    if analyze.in_ignore_file(fname, ignore_file):
        logging.info("Ignoring %s based on %s", fname, ignore_file)
        return ""

    with open(fname, "wb") as download_file:
        logging.info("Writing %s", fname)
        req.raw.decode_content = True
        shutil.copyfileobj(req.raw, download_file)

    return fname


def get_feed(feed_url: Text) -> Any:
    """Download and parse a feed"""

    feed_url = feed_url.strip()

    logging.info("Opening feed : %s", feed_url)

    req = requests.get(feed_url, headers=default_headers(), verify=False, timeout=60)

    return feedparser.parse(req.text)


def default_headers() -> Dict:
    """ Return default headers with a custom user agent """

    headers = requests.utils.default_headers()  # type: ignore
    headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/74.0.3729.169 Safari/537.36'})  # Chrome v74 2020-06-25

    return cast(Dict, headers)


def handle_feed(args: argparse.Namespace,
                feed_url: Text,
                partial: bool) -> Tuple[Text, Text, List[Text]]:
    """Take a feed, extract all entries, download the full original
    web page if partial , extract links and download any documents references
    if specified in the arguments and write the feed entry content
    to disk together with a meta data json file"""

    feed = get_feed(feed_url)

    if not feed:
        return "NOT FEED", feed_url, []

    files = []

    logging.info("%s contains %s entries",
                 feed_url,
                 len(feed["entries"]))

    for entry_n, entry in enumerate(feed["entries"]):
        logging.info("Handling : %s of %s : %s",
                     entry_n, len(feed["entries"]), entry['title'])

        if partial:
            filename, html_data = extract.entry_text_to_file(args, entry)
            files.append(filename)
        else:
            filename, html_data = extract.partial_entry_text_to_file(args, entry)
            files.append(filename)

        if not (filename and html_data):
            continue

        links = extract.get_links(entry, html_data)
        for link in analyze.filter_links(args, links):
            filename = download_and_store(feed_url, args.ignore, args.store_path, link)
            if filename:
                files.append(filename)
            else:
                logging.info("Unable to download and store %s", link)

    return "OK", feed_url, files


def download_feed_list(
        args: argparse.Namespace,
        feed_list: List[Text],
        partial: bool) -> List[Text]:

    """Download and analyze a list of feeds concurrently"""

    files: List[Text] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(handle_feed, args, url, partial): url
                         for url in feed_list}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result, feed, files = future.result()
            except Exception as exc:  # pylint: disable=W0703
                logging.error('%r generated an exception: %s', url, exc)
                exc_info = (type(exc), exc, exc.__traceback__)
                logging.error('Exception occurred', exc_info=exc_info)
            else:
                logging.info("%s returned %s",
                             feed,
                             result)

    return files
