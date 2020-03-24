
import addict
from act.scio.plugins import sectors
import os
import pytest


@pytest.mark.asyncio
async def test_sectors() -> None:
    """ test for plugins """

    prior_result = addict.Dict()
    prior_result.pos_tag = addict.Dict()
    prior_result.pos_tag.tokens = [('The', 'DT'), ('companies', 'NNS'), ('in', 'IN'), ('the', 'DT'), ('Bus', 'NNP'), (';', ':'), ('Finanical', 'NNP'), (',', ','), ('Aviation', 'NNP'), ('and', 'CC'), ('Automobile', 'NNP'), ('industry', 'NN'), ('is', 'VBZ'), ('in', 'IN'), ('trouble', 'NN'), ('.', '.')]

    test_text = 'The companies in the Bus; Finanical, Aviation and Automobile industry are large.'

    plugin = sectors.Plugin()
    plugin.configdir = os.path.join(os.path.dirname(__file__), "../act/scio/etc/plugins")
    res = await plugin.analyze(test_text, prior_result)

    assert 'aerospace' in res.result.sectors
    assert 'automotive' in res.result.sectors
    assert 'finanical' not in res.result.sectors
    assert 'finanical' not in res.result.unknown_sectors
