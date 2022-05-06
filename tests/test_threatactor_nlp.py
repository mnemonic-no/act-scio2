import os

import addict
import pytest

from act.scio.plugins import threatactor_nlp


@pytest.mark.asyncio  # type: ignore
async def test_sectors() -> None:
    """test for plugins"""

    nlpdata = addict.Dict()
    nlpdata.pos_tag = addict.Dict()
    nlpdata.pos_tag.tokens = [
        ["The", "DT"],
        ["Noughty", "NNP"],
        ["Noo-Noo", "NNP"],
        ["threat", "NN"],
        ["group", "NN"],
        ["sucks", "VBZ"],
        ["up", "RP"],
        ["tubby", "JJ"],
        ["toast", "NN"],
        [".", "."],
        ["The", "DT"],
        ["Tinky", "NNP"],
        ["Winky", "NNP"],
        [",", ","],
        ["Dipsy", "NNP"],
        [",", ","],
        ["Laa-Laa", "NNP"],
        ["and", "CC"],
        ["Poo", "NNP"],
        ["adversary", "JJ"],
        ["groups", "NNS"],
        ["looks", "VBZ"],
        ["sketchy", "NNS"],
        [".", "."],
    ]

    nlpdata.content = (
        "The Noughty Noo-Noo threat group sucks up tubby toast. "
        + "The Tinky Winky, Dipsy, Laa-Laa and Poo adversary groups looks sketchy."
    )

    plugin = threatactor_nlp.Plugin()
    plugin.configdir = os.path.join(
        os.path.dirname(__file__), "../act/scio/etc/plugins"
    )
    res = await plugin.analyze(nlpdata)

    tas = ["Noughty Noo-Noo", "Tinky Winky", "Dipsy", "Laa-Laa", "Poo"]

    for ta in tas:
        assert ta in res.result.actors
