import addict
from act.scio.aliasregex import normalize
from act.scio.vocabulary import Vocabulary
from act.scio.plugin import BasePlugin, Result
from typing import Text, List
import configparser
import os.path


def normalize_ta(name: Text, uppercase_abbr: List[Text]) -> Text:
    """Normalize TA names. Words are capitalized unless configured
    to be excempt"""

    res: Text = normalize(
        name,
        capitalize=True,
        uppercase_abbr=uppercase_abbr,
    )

    return res


class Plugin(BasePlugin):
    name = "threatactor"
    info = "Extracting references to known threat actors from a body of text"
    version = "0.2"
    dependencies: List[Text] = []

    async def analyze(self, nlpdata: addict.Dict) -> Result:

        ini = configparser.ConfigParser()
        ini.read([os.path.join(self.configdir, "threatactor_pattern.ini")])
        ini['threat_actor']['alias'] = os.path.join(self.configdir, ini['threat_actor']['alias'])

        uppercase_abbr = [x.strip() for x in ini['threat_actor'].get('uppercase_abbr', "").split("|")]
        vocab = Vocabulary(ini['threat_actor'])

        res = addict.Dict()

        res.ThreatActors = vocab.regex_search(
            nlpdata.content,
            normalize_result=(lambda x: normalize_ta(x, uppercase_abbr)),
            debug=self.debug)

        return Result(name=self.name, version=self.version, result=res)
