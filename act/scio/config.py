"""Copyright 2020 mnemonic AS <opensource@mnemonic.no>

Permission to use, copy, modify, and/or distribute this software for
any purpose with or without fee is hereby granted, provided that the
above copyright notice and this permission notice appear in all
copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

---
Config utilities for scio
"""

import os


def get_cache_dir(cache_id: str, create: bool = False) -> str:
    """
    Get cache dir.

    Honors $XDG_CACHE_HOME, but fallbacks to $HOME/.cache

Args:
    cache_id [str]: directory under CACHE that will be used
    create [bool]: create directory if not exists

Return path to cache_directory
    """

    home = os.environ["HOME"]

    cache_home = os.environ.get("XDG_CACHE_HOME", os.path.join(home, ".cache"))
    cache_dir = os.path.join(cache_home, cache_id)

    if create and not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    return cache_dir
