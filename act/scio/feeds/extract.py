"""Helper function for data extraction"""

import argparse
import html
import logging
import os.path
import urllib.parse
import uuid
from typing import Dict, List, Optional, Text, Tuple

import justext
import requests
from bs4 import BeautifulSoup

from act.scio.feeds import analyze, download


def get_content_from_entry(entry: Dict) -> Text:
    """Extract and concatenate the content portion of a feed entry"""

    if "content" in entry:
        return "\n".join([x["value"] for x in entry["content"]])

    logging.warning("No content for %s", entry["link"])

    return ""


def get_summary_from_entry(entry: Dict) -> Text:
    """Extract summary from feed entry"""

    if "summary_detail" in entry:
        value: Text = entry["summary_detail"]["value"]
        return value
    return ""


def create_html(entry: Dict) -> Text:
    """Wrap an entry in html headers and footers"""

    html_data = """<html>
    <head>
        <title>{title}</title>
    </head>
    <body>
        <p>
        {summary}
        </p>
        {content}
    </body>
</html>"""

    content = get_content_from_entry(entry)
    summary = get_summary_from_entry(entry)

    return html_data.format(
        title=entry.get("title", "NO TITLE"), content=content, summary=summary
    )


def replace_unsafe_filename_characters(path: Text) -> Text:
    """Make filename safe by only allowing alpha numeric characters,
    digits and ._-"""

    def _safe_char(c: Text) -> Text:
        if c.isalpha():
            return c
        if c.isdigit():
            return c
        if c in "_-.":
            return c
        if c in " \t":
            return "_"
        return ""

    return "".join(_safe_char(c) for c in path)


def read_stoplist(fname: Text) -> frozenset:
    """Take a list of words (one pr. line) and create a frozenset
    for use as stopwords when extracting text with jusText"""

    with open(fname, "r", encoding="utf-8") as stream:
        return frozenset(line.strip().lower() for line in stream)


def sanitize_filename(filename: Text) -> Text:
    """make sure that the filename is usable"""

    # make sure that the basename is less than 255 characters
    basename = os.path.basename(filename)
    directory = os.path.dirname(filename)
    if len(basename) >= 255:
        filename, extension = os.path.splitext(basename)
        basename = filename[: 254 - len(extension)] + extension

    return os.path.join(directory, basename)


def create_storage_path(filename: Text, extension: Text, *path_elements: Text) -> Text:
    """Build a path, sanitize filenames and build proper path structure"""

    if not extension.startswith("."):
        extension = "." + extension

    return sanitize_filename(
        os.path.join(
            *path_elements, replace_unsafe_filename_characters(filename) + extension
        )
    )


def partial_entry_text_to_file(
    args: argparse.Namespace, entry: Dict
) -> Tuple[Optional[Text], Optional[Text]]:
    """Download the original content and write it to the proper file.
    Return the html."""

    if "link" not in entry:
        logging.warning("entry does not contain 'link'")
        return None, None

    url = entry["link"]

    req = requests.get(
        url,
        proxies=download.proxies(args.proxy_string),
        headers=download.default_headers(),
        verify=False,
        timeout=60,
    )

    if req.status_code >= 400:
        logging.warning("Unable to download content: %s", url)
        return None, None

    filename = entry.get("title", str(uuid.uuid4()))

    html_data = "<html>\n<head>\n"
    html_data += "<title>{0}</title>\n</head>\n".format(entry.get("title", "NO TITLE"))
    html_data += "<body>\n"

    raw_html = req.text

    stoplist = (
        read_stoplist(args.stoplist)
        if args.stoplist
        else justext.get_stoplist("English")
    )

    paragraphs = justext.justext(raw_html, stoplist)

    for para in paragraphs:
        if not para.is_boilerplate:
            if para.is_heading:
                html_data += "\n<h1>{0}</h1>\n".format(html.escape(para.text))
            else:
                html_data += "<p>\n{0}\n</p>\n".format(html.escape(para.text))

    html_data += "\n</body>\n</html>"

    full_filename = create_storage_path(filename, "html", args.store_path, download)

    with open(full_filename, "w", encoding="utf-8") as html_file:
        html_file.write(html_data)

    # we want to return the raw_html and not the "article extraction"
    # since we want to extract links to .pdfs etc.
    return full_filename, raw_html


def entry_text_to_file(
    args: argparse.Namespace, entry: Dict
) -> Tuple[Optional[Text], Optional[Text]]:
    """Extract the entry content and write it to the proper file.
    Return the wrapped HTML"""

    filename = entry.get("title", str(uuid.uuid4()))

    html_data = create_html(entry)

    full_filename = create_storage_path(filename, "html", args.store_path, download)

    with open(full_filename, "w", encoding="utf-8") as html_file:
        html_file.write(html_data)

    return full_filename, html_data


def get_links(entry: Dict, html_data: Text) -> List[urllib.parse.ParseResult]:
    """Extract any links from the html"""

    links = []
    soup = BeautifulSoup(html_data, "html.parser")
    if soup:
        links = [a["href"] for a in soup.findAll("a", href=True)]
    else:
        logging.warning("soup is none : %s", entry.get("title", "NO TITLE"))

    return [analyze.parse_and_correct_link(link) for link in links]
