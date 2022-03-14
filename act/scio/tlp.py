from typing import Text, get_args

from pydantic.typing import Literal

TLP = Literal["RED", "AMBER", "GREEN", "WHITE"]


def valid_tlp(tlp: Text) -> bool:
    return tlp in get_args(TLP)
