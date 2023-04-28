import configparser
import json
import os.path
from typing import List
import openai

import addict

from act.scio.plugin import BasePlugin, Result


def openai_query(apikey: str, model: str, query: str) -> str:
    openai.api_key = apikey

    completion = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": query}],
    )
    content = completion.choices[0].message.content

    # TODO - handle json decode errors
    return json.loads(content)


class Plugin(BasePlugin):
    name = "threatactor_gpt"
    info = "GPT-Turbo experimental plugin"
    version = "0.1"
    dependencies: List[str] = []

    async def analyze(self, nlpdata: addict.Dict) -> Result:
        ini = configparser.ConfigParser()
        ini.read([os.path.join(self.configdir, "threatactor_gpt.ini")])

        apikey = ini["threat_actor_gpt"].get("apikey", None)
        model = ini["threat_actor_gpt"].get("model", "gpt-3.5-turbo")

        res = addict.Dict()

        res.ThretActor_Techniques = openai_query(
            apikey,
            model,
            f"""
        Enter the role as senior cyber threat intelligence analyst.
        Can you summarize the MITRE ATT&CK techniques per threat actor in the
        following text?
        Give the reponse in JSON format, where the key should be the threat actor names. The values should be a list of dicttionaries that summarize a specified technique. It should have the following keys:
        - techniqueID: MITRE ATT&CK technique ID
        - techniqueName: MITRE ATT&CK technique name
        - excerpt: excerpt from the text linked to this technique
        Do not repeat the question and be concise.
        Only include MITRE ATT&CK techniques and subtechniques.

        {nlpdata.content}""",
        )

        # res.ThreatActor_Sectors = openai_query(
        #     apikey,
        #     model,
        #     f"""
        # Enter the role as seniored cyber threat intelligence analyst.
        # Can you summarize the sectors targeted per threat actors mentioned in the following text?
        # Give the reponse in JSON format, where the key should be the threat actor name. The values should be the most specific industry sector that is targeted by the threat actor and the most specofic from this list: agriculture, automotive, chemical, commercial, communications, construction, defense, education, energy, entertainment, financial-services, government, government-emergency-services, government-local, government-national, government-public-services, government-regional, healthcare, hospitality-leisure, infrastructure, infrastructure-nuclear, infrastructure-water, infrastucture-dams, insurance, manufacturing, mining, non-profit, pharmaceuticals, retail, technology, telecommunications, transportation or utilities.
        #
        # {nlpdata.content}""",
        # )
        #
        return Result(name=self.name, version=self.version, result=res)
