import os

import addict
import pytest

from act.scio.plugins import locations


@pytest.mark.asyncio  # type: ignore
async def test_locations() -> None:
    """test for plugins"""

    nlpdata = addict.Dict()
    nlpdata.content = (
        "The Democratic Republic of Congo and the Arabic Emirates.\n\n"
        + "In London, people eat a lot of fish and chips.\n\n"
        + "England and Scotland is part of the UK.\n"
    )
    nlpdata.pos_tag = addict.Dict()
    nlpdata.pos_tag.tokens = [
        ("The", "DT"),
        ("Democratic", "JJ"),
        ("Republic", "NNP"),
        ("of", "IN"),
        ("Congo", "NNP"),
        ("and", "CC"),
        ("the", "DT"),
        ("Arabic", "NNP"),
        ("Emirates", "NNP"),
        (".", "."),
        ("In", "IN"),
        ("London", "NNP"),
        (",", ","),
        ("people", "NNS"),
        ("eat", "VBP"),
        ("a", "DT"),
        ("lot", "NN"),
        ("of", "IN"),
        ("fish", "JJ"),
        ("and", "CC"),
        ("chips", "NNS"),
        (".", "."),
        ("England", "NNP"),
        ("and", "CC"),
        ("Scotland", "NNP"),
        ("is", "VBZ"),
        ("part", "NN"),
        ("of", "IN"),
        ("the", "DT"),
        ("UK", "NNP"),
        (".", "."),
    ]

    plugin = locations.Plugin()
    plugin.configdir = os.path.join(
        os.path.dirname(__file__), "../act/scio/etc/plugins"
    )
    res = await plugin.analyze(nlpdata)

    for country in ["UK", "Republic of Congo", "England", "Scotland", "Congo"]:
        assert country in res.result.countries_mentioned

    assert "London" in [x.name for x in res.result.cities]
    assert "Congo" in [x.name for x in res.result.countries]
    assert "United Kingdom of Great Britain and Northern Ireland" in [
        x.name for x in res.result.countries_inferred
    ]
