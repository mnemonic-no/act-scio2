import addict
from act.scio.vocabulary import Vocabulary
from act.scio.plugin import BasePlugin, Result
from typing import Text, List
import configparser
import os.path


class Plugin(BasePlugin):
    name = "tools"
    info = "Extracting references to known tools from a body of text"
    version = "0.2"
    dependencies: List[Text] = []

    async def analyze(self, nlpdata: addict.Dict) -> Result:

        ini = configparser.ConfigParser()
        ini.read([os.path.join(self.configdir, "tools_pattern.ini")])
        ini['tools']['alias'] = os.path.join(self.configdir, ini['tools']['alias'])

        vocab = Vocabulary(ini['tools'])

        res = addict.Dict()

        res.Tools = vocab.regex_search(nlpdata.content, debug=self.debug)

        return Result(name=self.name, version=self.version, result=res)
