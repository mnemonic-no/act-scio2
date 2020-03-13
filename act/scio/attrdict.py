from typing import Any


class AttrDict(dict):
    "Dict like object that supports setattr() getattr()"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(AttrDict, self).__init__(*args, **kwargs)

    def __setattr__(self, key: Any, value: Any) -> None:
        self[key] = value

    def __getattr__(self, key: Any) -> Any:
        if key not in self:
            raise KeyError(f"'{key}'")
        return self[key]
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)
