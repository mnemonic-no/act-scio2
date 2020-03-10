"Alias regex tests"
from act.scio.aliasregex import normalize


def test_aliasregex_normalization() -> None:
    "Normalize test"

    assert normalize("oceanlotusGroup") == "oceanlotus group"
    assert normalize("APT 27") == "apt 27"
    assert normalize("APT.27") == "apt 27"
    assert normalize("APT-27") == "apt 27"
    assert normalize("APT- 27") == "apt 27"
    assert normalize("winntiGroup") == "winnti group"
