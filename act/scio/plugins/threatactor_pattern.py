from act.scio.attrdict import AttrDict
from act.scio.vocabulary import Vocabulary
from act.scio.plugin import BasePlugin, Result
from typing import Text, List
import configparser
import logging
import os.path


class Plugin(BasePlugin):
    name = "threatactor"
    info = "Extracting references to known threat actors from a body of text"
    version = "0.1"
    dependencies: List[Text] = []

    async def analyze(self, text: Text, prior_result: AttrDict) -> Result:

        ini = configparser.ConfigParser()
        ini.read([os.path.join(self.configdir, "threatactor_pattern.ini")])
        ini['threat_actor']['alias'] = os.path.join(self.configdir, ini['threat_actor']['alias'])

        vocab = Vocabulary(AttrDict(ini['threat_actor']))

        tas = []
        for regex in vocab.regex:
            for match in regex.findall(text):
                tas.append(match)
                if self.debug:
                    logging.info("%s found by regex %s", match, regex)

        res = AttrDict()

        res.ThreatActors = tas

        return Result(name=self.name, version=self.version, result=res)
