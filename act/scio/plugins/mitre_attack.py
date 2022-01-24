"""plugin module to extract MITRE Att&ck IDs from documents"""

import re
from typing import List, Text

import addict

from act.scio.plugin import BasePlugin, Result


class Plugin(BasePlugin):  # pylint: disable=r0903
    """Scio2 plugin"""

    name = "mitre_attack"
    info = "References to MITRE Att&ck IDs"
    version = "0.1"
    dependencies: List[Text] = []

    tactic_re = re.compile(r"\bTA[0-9]{4}\b")
    technique_re = re.compile(r"\bT[0-9]{4}(?!\.[0-9]{3})\b")
    subtechnique_re = re.compile(r"\bT[0-9]{4}\.[0-9]{3}\b")
    software_re = re.compile(r"\bS[0-9]{4}\b")
    group_re = re.compile(r"\bG[0-9]{4}\b")

    async def analyze(self, nlpdata: addict.Dict) -> Result:

        res = addict.Dict()

        res.Groups = self.group_re.findall(nlpdata.content)
        res.Tactics = self.tactic_re.findall(nlpdata.content)
        res.Techniques = self.technique_re.findall(nlpdata.content)
        res.SubTechniques = self.subtechnique_re.findall(nlpdata.content)
        res.Software = self.software_re.findall(nlpdata.content)

        return Result(name=self.name, version=self.version, result=res)
