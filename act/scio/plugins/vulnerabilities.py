import re
from typing import List, Text

import addict

from act.scio.plugin import BasePlugin, Result


class Plugin(BasePlugin):
    name = "vulnerabilities"
    info = "Extracting Vulnerability References (CVE, MSID) from body of text"
    version = "0.1"
    dependencies: List[Text] = []

    cve = re.compile(r"\b(?:CVE|cve)-\d{4}-\d{4,7}\b")
    msid = re.compile(r"\b(?:MS|ms)\d{2}-\d+\b")

    async def analyze(self, nlpdata: addict.Dict) -> Result:

        text = nlpdata.content

        res = addict.Dict()

        res.cve = self.cve.findall(text)
        res.msid = self.msid.findall(text)

        return Result(name=self.name, version=self.version, result=res)
