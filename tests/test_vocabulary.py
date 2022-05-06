"""
Vocabulary tests
"""

import os
from typing import List, Text

import addict

from act.scio.alias import parse_aliases
from act.scio.aliasregex import normalize
from act.scio.vocabulary import Vocabulary

VOCABULARY_DATADIR = os.path.join(os.path.dirname(__file__), "vocabulary")


def test_vocabulary_sector() -> None:
    """Sector tests"""

    config = addict.Dict()
    config.alias = os.path.join(VOCABULARY_DATADIR, "sector_aliases.cfg")
    config.key_mod = "stem"
    config.primary = True

    sector = Vocabulary(config)

    assert sector["defense"] == "defence"
    assert sector.get("defense", primary=False) == "defense"
    assert sector["not_exists"] is None


def normalize_ta(name: Text) -> Text:
    return normalize(
        name,
        capitalize=True,
        uppercase_abbr=["APT", "BRONZE", "IRON", "GOLD"],
    )


def test_vocabulary_threat_actor() -> None:
    """Threat actor vocabulary tests"""

    config = addict.Dict()
    config.alias = os.path.join(VOCABULARY_DATADIR, "ta_aliases.cfg")
    config.regexfromalias = True
    config.regexmanual = r"""
        \b([a-zA-Z]{4,}\s?[-_. ](?:dragon|duke|falcon|cedar|viper|panda|bear|jackal|spider|chollima|kitten|tiger))\b
        \b((?:BRONZE|IRON|GOLD)(?:\s+|[-_.]+)[A-Z]{3,})\b"""  # noqa: E501

    ta = Vocabulary(config)

    matches: List[Text] = ta.regex_search(
        "Observed threat actors apt_32, apt_28 and Crazy Kitten",
        normalize_result=normalize_ta,
    )

    assert "APT 32" in matches
    assert "APT 28" in matches
    assert "Crazy Kitten" in matches

    assert ta.get("OceanLotus Group", primary=True) == "APT32"
    assert ta.get("OCEANLOTUS GROUP", key_mod="none") is None
    assert ta.get("oceanLotusGroup", key_mod="norm") == "OceanLotus Group"
    assert ta.get("aPT32", key_mod="lower") == "APT32"
    assert ta.get("OCEANLOTUS GROUP", primary=True) == "APT32"
    assert ta["OCEANLOTUS GROUP"] == "OceanLotus Group"
    assert ta["not_exists"] is None


def test_vocabulary_tool() -> None:
    """Tool vocabulary test"""

    config = addict.Dict()
    config.alias = os.path.join(VOCABULARY_DATADIR, "tool_aliases.cfg")

    tool = Vocabulary(config)

    assert tool.get("backdoor:java/adwind", primary=True) == "jrat"
    assert tool["backdoor:java/adwind"] == "backdoor:java/adwind"


def test_vocabulary_aliases() -> None:
    """Parse alias config test"""

    alias_line1 = "my\\:tool: "
    alias_line2 = "thetool: backdoor\\:java/adwind,comma\\,tool"

    assert parse_aliases(alias_line1)[0] == "my:tool"
    assert parse_aliases(alias_line2)[0] == "thetool"
    assert "backdoor:java/adwind" in parse_aliases(alias_line2)[1]
    assert "comma,tool" in parse_aliases(alias_line2)[1]
