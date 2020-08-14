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

---
Helper functions used for making desitions and modifications
"""

from typing import List, Text, Optional
import logging
import os
import urllib
import urllib.parse


def parse_and_correct_link(link: Text) -> urllib.parse.ParseResult:
    """Parse the link and rewrites known web-view vs raw store locations (e.g. github)"""

    parsed = urllib.parse.urlparse(link)

    if parsed.netloc == 'github.com':
        parsed = parsed._replace(netloc="raw.githubusercontent.com")
        parsed = parsed._replace(path=parsed.path.replace("/blob/", "/", 1))
        logging.info("found github link. Modify to get raw content")

    return parsed


def in_ignore_file(fname: Text, ignore_file: Optional[Text]) -> bool:
    """Check if a spesific filename is present in the ignore file (if any)"""

    if not ignore_file:
        return False

    if not os.path.isfile(ignore_file):
        logging.warning("Ignore file not found: %s", ignore_file)
        return False

    with open(ignore_file) as f:
        ignored = [line.strip() for line in f]
        if fname in ignored:
            return True

    return False


def extract_file_extension(url: urllib.parse.ParseResult) -> Text:
    """Extract the extension (if any) from the path.
    If there are no extension, return the empty string."""

    file_extension = url.path.rsplit(".", 1)
    if len(file_extension) == 2:
        return file_extension[1]
    return ""


def filter_links(file_formats: List[Text],
                 links: List[urllib.parse.ParseResult]) -> List[urllib.parse.ParseResult]:
    """Run though a list of urls, checking if they contains certain
    elements that looks like possible file download possibilities"""

    file_format_set = set(file_formats)

    def __contains_fileextension(url: urllib.parse.ParseResult) -> bool:
        ext = extract_file_extension(url)
        return ext in file_format_set

    return list(filter(__contains_fileextension, links))
