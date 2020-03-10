"""
Vocabulary tests
"""

from pathlib import Path

import act.scio.vocabulary as vocabulary
from act.scio.alias import parse_aliases


def test_vocabulary_sector():
    """ Sector tests """
    ini = Path(__file__).resolve().parent.parent.joinpath("vocabularies.ini").resolve()
    sector = vocabulary.from_config(ini)["sector"]

    assert sector["defense"] == "defence"
    assert sector.get("defense", primary=False) == "defense"
    assert sector["not_exists"] is None


def test_vocabulary_threat_actor():
    """ Threat actor vocabulary tests """
    ini = Path(__file__).resolve().parent.parent.joinpath("vocabularies.ini").resolve()
    ta = vocabulary.from_config(ini)["threat_actor"]

    assert ta.get("OceanLotus Group", primary=True) == "APT32"
    assert ta.get("OCEANLOTUS GROUP", key_mod="none") is None
    assert ta.get("oceanLotusGroup", key_mod="norm") == "OceanLotus Group"
    assert ta.get("OCEANLOTUS GROUP", primary=True) == "APT32"
    assert ta["OCEANLOTUS GROUP"] == "OceanLotus Group"
    assert ta["not_exists"] is None


def test_vocabulary_tool():
    """ Tool vocabulary test """
    ini = Path(__file__).resolve().parent.parent.joinpath("vocabularies.ini").resolve()
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
