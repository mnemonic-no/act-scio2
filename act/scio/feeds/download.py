"""Helper functions related to downloading feeds and files"""

import argparse
import concurrent.futures
import logging
import os.path
import shutil
import urllib.parse
from typing import Any, Dict, List, Optional, Text, Tuple, cast

import feedparser
import requests

from act.scio.feeds import analyze, extract


def download_and_store(
    feed_url: Text,
    ignore_file: Optional[Text],
    storage_path: Text,
    proxy_string: Optional[Text],
    link: urllib.parse.ParseResult,
) -> Dict[Text, Text]:
    """Download and store a link. Storage defined in args"""

    # check if the actual url is in the ignore file. If so, no download will take place.
    if analyze.in_ignore_file(link.geturl(), ignore_file):
        logging.info("Download link [%s] in ignore file.", link.geturl())
        return {}

    logging.info("downloading %s", link.geturl())

    # if netloc does not contain a hostname, assume a relative path to the feed url
    if link.netloc == "":
        parsed_feed_url = urllib.parse.urlparse(feed_url)
        link = link._replace(
            scheme=parsed_feed_url.scheme, netloc=parsed_feed_url.netloc, path=link.path
        )
        logging.info(
            "possible relative path %s, trying to append host: %s",
            link.path,
            parsed_feed_url.netloc,
        )

    try:
        req = requests.get(
            link.geturl(),
            proxies=proxies(proxy_string),
            headers=default_headers(),
            verify=False,
            stream=True,
            timeout=60,
        )
    except requests.exceptions.ReadTimeout:
        logging.info("%s timed out", link.geturl())
        return {}
    except requests.exceptions.ConnectionError:
        logging.info("%s connection error", link.geturl())
        return {}
    except requests.exceptions.MissingSchema:
        logging.info("%s missing schema", link.geturl())
        return {}

    if req.status_code >= 400:
        logging.info("Status %s - %s", req.status_code, link)
        return {}

    basename = os.path.basename(link.path)
    fname = extract.create_storage_path(basename, None, storage_path, "download")

    # check if the filename on disk is in the ignore file. If so, do not return filename
    # for upload. This differ from URL in the ignore file as the file is in fact downloaded by
    # the feed worker, but not uploaded to Scio.
    if analyze.in_ignore_file(basename, ignore_file):
        logging.info("Ignoring %s based on %s", fname, ignore_file)
        return {}

    with open(fname, "wb") as download_file:
        logging.info("Writing %s", fname)
        req.raw.decode_content = True
        shutil.copyfileobj(req.raw, download_file)

    return {"filename": fname, "uri": link.geturl()}


def get_feed(feed_url: Text, proxy_string: Optional[Text] = None) -> Any:
    """Download and parse a feed"""

    feed_url = feed_url.strip()

    logging.info("Opening feed : %s", feed_url)

    try:
        req = requests.get(
            feed_url,
            proxies=proxies(proxy_string),
            headers=default_headers(),
            verify=False,
            timeout=60,
        )
    except requests.exceptions.ReadTimeout:
        logging.error("%s timed out", feed_url)
        return None
    except requests.exceptions.ConnectionError:
        logging.error("%s connection error", feed_url)
        return None
    except requests.exceptions.MissingSchema:
        logging.error("%s missing schema", feed_url)
        return None

    return feedparser.parse(req.text)


def proxies(proxy_string: Optional[Text]) -> Optional[Dict[Text, Text]]:
    """Return proxy dict to be used by requests if proxy_string is set"""

    if proxy_string:
        return {"http": proxy_string, "https": proxy_string}
    return None


def default_headers() -> Dict[Text, Text]:
    """Return default headers with a custom user agent"""

    headers = requests.utils.default_headers()
    headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/74.0.3729.169 Safari/537.36"
        }
    )  # Chrome v74 2020-06-25

    return cast(Dict[Text, Text], headers)


def handle_feed(
    args: argparse.Namespace, feed_url: Text, partial: bool
) -> Tuple[Text, Text, List[Dict[Text, Text]]]:
    """Take a feed, extract all entries, download the full original
    web page if partial , extract links and download any documents references
    if specified in the arguments and write the feed entry content
    to disk together with a meta data json file"""

    feed = get_feed(feed_url, args.proxy_string)

    if not feed:
        return "NOT FEED", feed_url, []

    files: List[Dict[Text, Text]] = []

    logging.info("%s contains %s entries", feed_url, len(feed["entries"]))

    for entry_n, entry in enumerate(feed["entries"]):
        logging.info(
            "Handling : %s of %s : %s",
            entry_n,
            len(feed["entries"]),
            entry.get("title", f"No title : {feed_url}"),
        )

        filename, html_data = (
            extract.partial_entry_text_to_file(args, entry)
            if partial
            else extract.entry_text_to_file(args, entry)
        )
        if filename:
            entry = {"filename": filename, "uri": feed_url}
            files.append(entry)
            logging.debug("Added entry %s to list of files", entry)
        else:
            logging.info(
                'entry "%s" [partial=%s] returned no filename',
                entry.get("title", "NA"),
                partial,
            )

        if not (filename and html_data):
            continue

        links = extract.get_links(entry, html_data)

        # Download all urls that looks like they have the correct file extension
        # and add the filenames of the downloaded files to the list of candidates
        # to upload.
        files.extend(
            download_and_store(
                feed_url, args.ignore, args.store_path, args.proxy_string, link
            )
            for link in analyze.filter_links(
                args.file_format, links, args.exclude_filenames
            )
        )

    return "OK", feed_url, list(filter(None, files))


def download_feed_list(
    args: argparse.Namespace, feed_list: List[Text], partial: bool
) -> List[Dict[Text, Text]]:

    """Download and analyze a list of feeds concurrently"""

    files: List[Dict[Text, Text]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {
            executor.submit(handle_feed, args, url, partial): url for url in feed_list
        }
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            result, feed, feed_files = future_result_exception(url, future)
            logging.info(
                "Feed[%s] (%s) returned %s with %s files", feed, url, result, len(files)
            )
            files += feed_files

    return files


def future_result_exception(
    url: Text, future: concurrent.futures.Future  # type: ignore
) -> Tuple[Text, Text, List[Dict[Text, Text]]]:
    """Retrieve the result of a future, logging any exception"""

    try:
        result, feed, files = future.result()
        logging.info("%s returned %s", feed, result)
        return result, feed, files
    except Exception as exc:  # pylint: disable=W0703
        logging.error("%r generated an exception: %s", url, exc)
        exc_info = (type(exc), exc, exc.__traceback__)
        logging.error("Exception occurred", exc_info=exc_info)
        return "EXCEPTION", "NA", []
