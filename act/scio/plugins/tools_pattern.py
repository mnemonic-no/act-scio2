import configparser
import os.path
from typing import List, Text

import addict

from act.scio.plugin import BasePlugin, Result
from act.scio.vocabulary import Vocabulary


class Plugin(BasePlugin):
    name = "tools"
    info = "Extracting references to known tools from a body of text"
    version = "0.2"
    dependencies: List[Text] = []

    async def analyze(self, nlpdata: addict.Dict) -> Result:

        ini = configparser.ConfigParser()
        ini.read([os.path.join(self.configdir, "tools_pattern.ini")])
        ini["tools"]["alias"] = os.path.join(self.configdir, ini["tools"]["alias"])

        vocab = Vocabulary(ini["tools"])

        res = addict.Dict()

        res.Tools = vocab.regex_search(nlpdata.content, debug=self.debug)

        return Result(name=self.name, version=self.version, result=res)
