import os

import addict
import pytest

from act.scio.plugins import threatactor_pattern


@pytest.mark.asyncio  # type: ignore
async def test_threatactor_pattern() -> None:
    """test for plugins"""

    nlpdata = addict.Dict()

    nlpdata.content = """

    Lorem Ipsum Dirty Panda, APT1 APT-2, Apt 35, APT_46, UNC2354

    The threat actors aqua blizzard was previous known as ACTINIUM

    Pumpkin Sandstorm was known as DEV-0146

    DEV-0257 is know renamed to Storm-0257.

    """

    plugin = threatactor_pattern.Plugin()
    plugin.configdir = os.path.join(
        os.path.dirname(__file__), "../act/scio/etc/plugins"
    )
    res = await plugin.analyze(nlpdata)

    assert "Dirty Panda" in res.result.ThreatActors
    assert "APT 1" in res.result.ThreatActors
    assert "APT 2" in res.result.ThreatActors
    assert "APT 35" in res.result.ThreatActors
    assert "APT 46" in res.result.ThreatActors
    assert "UNC 2354" in res.result.ThreatActors
    assert "Aqua Blizzard" in res.result.ThreatActors
    assert "Pumpkin Sandstorm" in res.result.ThreatActors
    assert "Storm-0257" in res.result.ThreatActors
