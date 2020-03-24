import addict
import nltk
from act.scio.plugin import BasePlugin, Result
from typing import Text, List


class Plugin(BasePlugin):
    name = "pos_tag"
    info = "Part-of-speach tagging of a body of text"
    version = "0.1"
    dependencies: List[Text] = []

    async def analyze(self, text: Text, prior_result: addict.Dict) -> Result:

        res = addict.Dict()

        tokens = nltk.word_tokenize(text)

        res.tokens = nltk.pos_tag(tokens)

        return Result(name=self.name, version=self.version, result=res)
