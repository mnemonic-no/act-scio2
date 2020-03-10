from typing import Dict, List, Text

from act.scio.attrdict import AttrDict
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
        result = AttrDict()
        result.split = [s.strip() for s in text.split(".") if s.strip()]
        return Result(
            name=self.name,
            version=self.version,
            result=result)
