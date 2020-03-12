"""
Vocabulary tests
"""

import os

from act.scio.vocabulary import Vocabulary
from act.scio.alias import parse_aliases
from act.scio.attrdict import AttrDict


def test_vocabulary_sector():
    """ Sector tests """
    ini = Path(__file__).resolve().parent.joinpath("vocabulary/vocabularies.ini").resolve()
    sector = vocabulary.from_config(ini)["sector"]

    assert sector["defense"] == "defence"
    assert sector.get("defense", primary=False) == "defense"
    assert sector["not_exists"] is None


def test_vocabulary_threat_actor():
    """ Threat actor vocabulary tests """

    test_datadir = os.path.join(os.path.dirname(__file__), "vocabulary")

    config = AttrDict()

    config.alias = os.path.join(test_datadir, "ta_aliases.cfg")
    config.regexmanual = True
    config.regexmanual = r'''
        \b([a-zA-Z]{4,}\s?[-_. ](?:dragon|duke|falcon|cedar|viper|panda|bear|jackal|spider|chollima|kitten|tiger))\b
        \b((?:BRONZE|IRON|GOLD)(?:\s+|[-_.]+)[A-Z]{3,})\b'''

    ta = Vocabulary(config)

    assert ta.get("OceanLotus Group", primary=True) == "APT32"
    assert ta.get("OCEANLOTUS GROUP", key_mod="none") is None
    assert ta.get("oceanLotusGroup", key_mod="norm") == "OceanLotus Group"
    assert ta.get("OCEANLOTUS GROUP", primary=True) == "APT32"
    assert ta["OCEANLOTUS GROUP"] == "OceanLotus Group"
    assert ta["not_exists"] is None


def test_vocabulary_tool():
    """ Tool vocabulary test """
    ini = Path(__file__).resolve().parent.joinpath("vocabulary/vocabularies.ini").resolve()
    tool = vocabulary.from_config(ini)["tool"]

    assert tool.get("backdoor:java/adwind", primary=True) == "adwind"
    assert tool["backdoor:java/adwind"] == "backdoor:java/adwind"


def test_vocabulary_aliases():
    """ Parse alias config test """

    alias_line1 = "my\\:tool: "
    alias_line2 = "thetool: backdoor\\:java/adwind,comma\\,tool"

    assert parse_aliases(alias_line1)[0] == "my:tool"
    assert parse_aliases(alias_line2)[0] == "thetool"
    assert "backdoor:java/adwind" in parse_aliases(alias_line2)[1]
    assert "comma,tool" in parse_aliases(alias_line2)[1]
