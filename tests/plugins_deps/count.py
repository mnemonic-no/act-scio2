from typing import Dict, List, Text

import addict
from act.scio.plugin import BasePlugin, Result


class Plugin(BasePlugin):
    name = "count"
    info = "test deps info"
    version = "0.1"
    dependencies: List[Text] = ["sentences"]

    async def analyze(self, text: Text, prior_result: Dict) -> Result:
        return Result(
            name=self.name,
            version=self.version,
            result=addict.Dict({s: len(s) for s in prior_result["sentences"]["split"]}))
