import os

import addict
import pytest

from act.scio.plugins import vulnerabilities


@pytest.mark.asyncio  # type: ignore
async def test_vulnerabilites() -> None:
    """test for plugins"""

    nlpdata = addict.Dict()
    nlpdata.content = """
    CVE-1991-1234 lorem ipsum
    CVE-1992-12345 lorem ipsum
    CVE-1993-123456 lorem ipsum
    CVE-1994-1234567 lorem ipsum
    CVE-1995-12345678 lorem ipsum
    CVE-1994-12 lorem ipsum
    CVE-123-1234 lorem ipsum
    MS15-132 lorem ipsum
    """

    plugin = vulnerabilities.Plugin()
    plugin.configdir = os.path.join(
        os.path.dirname(__file__), "../act/scio/etc/plugins"
    )
    res = await plugin.analyze(nlpdata)

    assert "CVE-1991-1234" in res.result.cve
    assert "CVE-1992-12345" in res.result.cve
    assert "CVE-1993-123456" in res.result.cve
    assert "CVE-1994-1234567" in res.result.cve
    assert "MS15-132" in res.result.msid
    assert "CVE-123-1234" not in res.result.cve
    assert "CVE-1994-12" not in res.result.cve
    assert "CVE-1995-12345678" not in res.result.cve
