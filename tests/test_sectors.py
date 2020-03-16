import pytest

from act.scio.attrdict import AttrDict
from act.scio.plugins import sectors


@pytest.mark.asyncio
async def test_sectors(monkeypatch) -> None:
    """ test for plugins """

    prior_result = AttrDict()
    prior_result.pos_tag = AttrDict()
    prior_result.pos_tag.tokens = [('The', 'DT'), ('companies', 'NNS'), ('in', 'IN'), ('the', 'DT'), ('Bus', 'NNP'), (';', ':'), ('Finanical', 'NNP'), (',', ','), ('Aviation', 'NNP'), ('and', 'CC'), ('Automobile', 'NNP'), ('industry', 'NN'), ('is', 'VBZ'), ('in', 'IN'), ('trouble', 'NN'), ('.', '.')]

    test_text = 'The companies in the Bus; Finanical, Aviation and Automobile industry are large.'

    plugin = sectors.Plugin()
    plugin.configdir = "act/scio/etc/plugins"
    res = await plugin.analyze(test_text, prior_result)

    assert 'aerospace' in res.result.sectors
    assert 'automotive' in res.result.sectors
    assert 'finanical' not in res.result.sectors
    assert 'finanical' not in res.result.unknown_sectors

