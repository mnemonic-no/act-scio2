from act.scio.attrdict import AttrDict
from act.scio.regexalias import normalize
from act.scio.vocabulary import Vocabulary
from act.scio.plugin import BasePlugin, Result
from typing import Text, List
import configparser
import os.path


def normalize_ta(name: Text) -> Text:
    return normalize(
        name,
        capitalize=True,
        uppercase_abbr=["APT", "BRONZE", "IRON", "GOLD"],
    )


class Plugin(BasePlugin):
    name = "threatactor"
    info = "Extracting references to known threat actors from a body of text"
    version = "0.2"
    dependencies: List[Text] = []

    async def analyze(self, text: Text, prior_result: AttrDict) -> Result:

        ini = configparser.ConfigParser()
        ini.read([os.path.join(self.configdir, "threatactor_pattern.ini")])
        ini['threat_actor']['alias'] = os.path.join(self.configdir, ini['threat_actor']['alias'])

        vocab = Vocabulary(AttrDict(ini['threat_actor']))

        res = AttrDict()

        res.ThreatActors = vocab.regex_search(
                text,
                normalize_result=normalize_ta,
                debug=self.debug)

        return Result(name=self.name, version=self.version, result=res)
