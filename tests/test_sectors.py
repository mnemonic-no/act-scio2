import os

import addict
import pytest

from act.scio.plugins import sectors


@pytest.mark.asyncio  # type: ignore
async def test_sectors() -> None:
    """test for plugins"""

    nlpdata = addict.Dict()
    nlpdata.pos_tag = addict.Dict()
    nlpdata.pos_tag.tokens = [
        ("The", "DT"),
        ("companies", "NNS"),
        ("in", "IN"),
        ("the", "DT"),
        ("Bus", "NNP"),
        (";", ":"),
        ("Finanical", "NNP"),
        (",", ","),
        ("Aviation", "NNP"),
        ("and", "CC"),
        ("Automobile", "NNP"),
        ("industry", "NN"),
        ("is", "VBZ"),
        ("in", "IN"),
        ("trouble", "NN"),
        (".", "."),
    ]

    nlpdata.content = (
        "The companies in the Bus; Finanical, "
        + "Aviation and Automobile industry are large."
    )

    plugin = sectors.Plugin()
    plugin.configdir = os.path.join(
        os.path.dirname(__file__), "../act/scio/etc/plugins"
    )
    res = await plugin.analyze(nlpdata)

    assert "aerospace" in res.result.sectors
    assert "automotive" in res.result.sectors
    assert "finanical" not in res.result.sectors
    assert "finanical" not in res.result.unknown_sectors
