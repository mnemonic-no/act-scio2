from typing import Dict, List, Text

import addict
from act.scio.plugin import BasePlugin, Result


class Plugin(BasePlugin):
    """
    Split by "." and return stripped, non-empty sentences.
    """
    name = "sentences"
    info = "test deps info"
    version = "0.1"
    dependencies: List[Text] = []

    async def analyze(self, text: Text, prior_result: Dict) -> Result:
        result = addict.Dict()
        result.split = [s.strip() for s in text.split(".") if s.strip()]
        return Result(
            name=self.name,
            version=self.version,
            result=result)
