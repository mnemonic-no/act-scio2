from typing import Text, List, Dict
from act.scio.plugin import BasePlugin, Result


class Plugin(BasePlugin):
    name = "test"
    info = "test info"
    version = "0.1"
    dependencies: List[Text] = []

    async def analyze(self, text: Text, prior_result: Dict) -> Result:
        return Result(name=self.name, version=self.version, result={"test": text})
