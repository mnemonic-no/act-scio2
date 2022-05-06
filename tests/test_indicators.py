""" Indicators test """

import os

import addict
import pytest

from act.scio.plugins import indicators

TEST_TEXT = """
    hXXp://my.test.no/hxxp/
    md5: be5ee729563fa379e71d82d61cc3fdcf lorem ipsum
    sha256: 103cb6c404ba43527c2deac40fbe984f7d72f0b2366c0b6af01bd0b4f1a30c74 lorem ipsum
    sha1: 3c07cb361e053668b4686de6511d6a904a9c4495 lorem ipsum
    %2fchessbase.com lorem ipsum
    %2Fchessbase.com lorem ipsum
    twitter.com lorem ipsum
    %2ftwitter.com lorem ipsum
    %2Ftwitter.com lorem ipsum
    127.0.0.1 lorem ipsum
    127[.]0[.]0[.]2 lorem ipsum
    127.0.0{.}3 lorem ipsum
    127.0.0\\.4 lorem ipsum
    ftp://files.example.com lorem ipsum
    https://www.vg.no/index.html?q=news#top lorem / ipsum
    HTTP://1.2.3.4/5-index.html / lorem ipsum
    hXXp://2.3.4.5/ lorem / ipsum
    hxxps://3.4.5.6 lorem ipsum
    4.5.6.7/gurba lorem ipsum
    5.6.7.8/9 lorem ipsum
    6.7.8.9/10 lorem ipsum
    www.nytimes3xbfgragh.onion lorem ipsum
    fe80::ea39:35ff:fe12:2d71/64 lorem ipsum
    The mail address user@fastmail.fm is not real
    www.mnemonic.no
    this.ends.in.tld.no."
"""


@pytest.mark.asyncio  # type: ignore
async def test_sectors() -> None:
    """test for plugins"""

    nlpdata = addict.Dict()
    plugin = indicators.Plugin()
    plugin.configdir = os.path.join(
        os.path.dirname(__file__), "../act/scio/etc/plugins"
    )

    nlpdata.content = TEST_TEXT

    res = await plugin.analyze(nlpdata)

    # print(res.result)

    assert res.result.md5 == ["be5ee729563fa379e71d82d61cc3fdcf"]
    assert res.result.sha256 == [
        "103cb6c404ba43527c2deac40fbe984f7d72f0b2366c0b6af01bd0b4f1a30c74"
    ]
    assert res.result.sha1 == ["3c07cb361e053668b4686de6511d6a904a9c4495"]

    assert "http://my.test.no/hxxp/" in res.result.uri
    assert "HTTP://1.2.3.4/5-index.html" in res.result.uri
    assert "https://3.4.5.6" in res.result.uri
    assert "www.mnemonic.no" in res.result.fqdn
    assert "chessbase.com" in res.result.fqdn
    assert "twitter.com" in res.result.fqdn
    assert "127.0.0.1" in res.result.ipv4
    assert "127.0.0.2" in res.result.ipv4
    assert "127.0.0.3" in res.result.ipv4
    assert "127.0.0.4" in res.result.ipv4
    assert "4.5.6.7" in res.result.ipv4
    assert "5.6.7.8/9" in res.result.ipv4net
    assert "user@fastmail.fm" in res.result.email
    assert "fe80::ea39:35ff:fe12:2d71" in res.result.ipv6
