""" test feed analyse """

import urllib.parse

from act.scio.feeds import analyze


def test_filter_links() -> None:
    """test that links filter works"""

    links = [
        "http://example.com/check.js",
        "https://example.com/some.pdf",
        "http://example.com/sitemap.xml",
    ]
    correct = ["https://example.com/some.pdf", "http://example.com/sitemap.xml"]

    parsed_links = [urllib.parse.urlparse(link) for link in links]
    parsed_correct = [urllib.parse.urlparse(link) for link in correct]

    assert parsed_correct == analyze.filter_links(["xml", "pdf"], parsed_links)


def test_filter_links_with_exlude() -> None:
    """test that links filter works"""

    links = [
        "http://example.com/check.js",
        "https://example.com/some.pdf",
        "http://example.com/sitemap.xml",
    ]
    correct = ["https://example.com/some.pdf"]

    parsed_links = [urllib.parse.urlparse(link) for link in links]
    parsed_correct = [urllib.parse.urlparse(link) for link in correct]

    assert parsed_correct == analyze.filter_links(
        ["xml", "pdf"], parsed_links, exclude_filenames=["sitemap.xml"]
    )
