""" test feed download """

import io
import os

import pytest

# Unfortunately not exported
from _pytest.monkeypatch import MonkeyPatch

from act.scio import analyze, plugin


@pytest.mark.asyncio  # type: ignore
async def test_plugins(monkeypatch: MonkeyPatch) -> None:
    """test for plugins"""

    plugin_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "plugins_deps"
    )

    plugins = plugin.load_external_plugins(plugin_dir)

    monkeypatch.setattr(
        "sys.stdin", io.StringIO("This is a test. And this is another one.")
    )

    res = await analyze.analyze(plugins, beanstalk_client=False)

    # Two plugins + text
    assert len(res.keys()) == 5

    assert "count" in res
    assert "sentences" in res

    assert len(res["count"]) == 2

    assert res["count"]["This is a test"] == 14
    assert res["count"]["And this is another one"] == 23
