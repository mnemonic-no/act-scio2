"""Helper function for data extraction"""

from typing import Dict, Text, Tuple, Optional, List
import logging
import argparse
import os.path
import urllib.parse

from bs4 import BeautifulSoup
import html
import justext
import requests

from act.scio.feeds import download, analyze


def get_content_from_entry(entry: Dict) -> Text:
    """Extract and concatenate the content portion of a feed entry"""

    if "content" in entry:
        return "\n".join([x["value"] for x in entry['content']])

    logging.warning("No content for %s", entry['link'])

    return ""


def get_summary_from_entry(entry: Dict) -> Text:
    """Extract summary from feed entry"""

    if "summary_detail" in entry:
        value: Text = entry['summary_detail']['value']
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

    return html_data.format(title=entry["title"],
                            content=content,
                            summary=summary)


def safe_filename(path: Text) -> Text:
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

    with open(fname, "r") as stream:
        return frozenset(line.strip().lower() for line in stream)


def partial_entry_text_to_file(
        args: argparse.Namespace,
        entry: Dict) -> Tuple[Optional[Text], Optional[Text]]:
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
        timeout=60)

    if req.status_code >= 400:
        logging.warning("Unable to download content: %s", url)
        return None, None

    filename = safe_filename(entry['title'])

    html_data = "<html>\n<head>\n"
    html_data += "<title>{0}</title>\n</head>\n".format(entry['title'])
    html_data += "<body>\n"

    raw_html = req.text

    stoplist = read_stoplist(args.stoplist) if args.stoplist else justext.get_stoplist('English')

    paragraphs = justext.justext(raw_html, stoplist)

    for para in paragraphs:
        if not para.is_boilerplate:
            if para.is_heading:
                html_data += "\n<h1>{0}</h1>\n".format(html.escape(para.text))
            else:
                html_data += "<p>\n{0}\n</p>\n".format(html.escape(para.text))

    html_data += "\n</body>\n</html>"

    full_filename = os.path.join(args.store_path, "download", filename + ".html")
    with open(full_filename, "w") as html_file:
        html_file.write(html_data)

    # we want to return the raw_html and not the "article extraction"
    # since we want to extract links to .pdfs etc.
    return full_filename, raw_html


def entry_text_to_file(
        args: argparse.Namespace,
        entry: Dict) -> Tuple[Optional[Text], Optional[Text]]:
    """Extract the entry content and write it to the proper file.
    Return the wrapped HTML"""

    filename = safe_filename(entry['title'])

    html_data = create_html(entry)

    full_filename = os.path.join(os.path.join(args.store_path, "download"), filename + ".html")
    with open(full_filename, "w") as html_file:
        html_file.write(html_data)

    return full_filename, html_data


def get_links(entry: Dict, html_data: Text) -> List[urllib.parse.ParseResult]:
    """Extract any links from the html"""

    links = []
    soup = BeautifulSoup(html_data, "html.parser")
    if soup:
        links = [a['href'] for a in soup.findAll('a', href=True)]
    else:
        logging.warning("soup is none : %s", entry['title'])

    return [analyze.parse_and_correct_link(link) for link in links]
