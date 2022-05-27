from typing import Text

from pydantic.typing import Literal  # type: ignore

TLP_ALLOWED_VALUES = ("RED", "AMBER", "GREEN", "WHITE")

TLP = Literal[TLP_ALLOWED_VALUES]


def valid_tlp(tlp: Text) -> bool:
    return tlp in TLP_ALLOWED_VALUES
