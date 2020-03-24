
from act.scio.attrdict import AttrDict
from act.scio.plugins import threatactor_pattern
import os
import pytest


@pytest.mark.asyncio
async def test_threatactor_pattern() -> None:
    """ test for plugins """

    nlpdata = AttrDict()

    nlpdata.text = '''Lorem Ipsum Dirty Panda, APT1 APT-2, Apt 35, APT_46'''

    plugin = threatactor_pattern.Plugin()
    plugin.configdir = os.path.join(os.path.dirname(__file__), "../act/scio/etc/plugins")
    res = await plugin.analyze(nlpdata)

    assert 'Dirty Panda' in res.result.ThreatActors
    assert 'APT 1' in res.result.ThreatActors
    assert 'APT 2' in res.result.ThreatActors
    assert 'APT 35' in res.result.ThreatActors
    assert 'APT 46' in res.result.ThreatActors
