import configparser
import json
from typing import List, Dict, Any, cast, Optional
import openai
from logging import warning, info

from pathlib import Path

from pydantic import BaseModel


import addict

from act.scio.plugin import BasePlugin, Result


DEFAULT_TLP = "AMBER"


class ArgumentException(Exception):
    pass


class OpenAIResult(BaseModel):
    query: str
    model: str
    answer_text: Optional[str] = None
    answer_json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def openai_query(
    apikey: str, model: str, query: str, content: str, format: str
) -> OpenAIResult:
    openai.api_key = apikey

    result = OpenAIResult(query=query, model=model)

    completion = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": f"{query}\n\n\n{content}"}],
    )
    content = completion.choices[0].message.content

    if format == "json":
        try:
            result.answer_json = cast(Dict[str, Any], json.loads(content))
        except json.decoder.JSONDecodeError:
            result.error = f"Unable to decode json: {content}"
    elif format == "text":
        result.answer_text = content

    else:
        raise ArgumentException(f"Illegal format: {format}")

    return result


class Plugin(BasePlugin):
    name = "openai"
    info = "OpenAI plugin"
    version = "0.1"
    dependencies: List[str] = []

    async def analyze(self, nlpdata: addict.Dict) -> Result:
        ini = configparser.ConfigParser()
        ini.read(Path(self.configdir) / "openai.ini")

        hexdigest = nlpdata.get("hexdigest", "UNKNOWN")

        if "tlp" not in nlpdata:
            doc_tlp = DEFAULT_TLP
            warning(
                f"TLP not specified in document {hexdigest}, set to '{DEFAULT_TLP}'"
            )
        else:
            doc_tlp = nlpdata["tlp"].upper()

        res = addict.Dict()

        for name in ini.sections():
            prompt = ini[name]

            # Get the list of TLPs per prompt. It will normally be specified in default
            # but with this technique we can overwrite it per promt if we want to
            tlp_list = {
                tlp.strip().upper()
                for tlp in prompt.get("tlp", "").split()
                if tlp.strip()
            }

            if doc_tlp not in tlp_list:
                info(
                    f"Skipping document {hexdigest}, TLP {doc_tlp} not in TLPs that "
                    f"should do do lookups ({', '.join(tlp_list)})"
                )
                continue

            if not prompt.get("apikey"):
                info(f"No apikey defined, skipping {name}")

            if not prompt.get("query"):
                warning(f"No query defined in {name}")
                continue

            # Strip whitespace at start/end of each line
            query = "\n".join(line.strip() for line in prompt.get("query").split("\n"))

            res[name] = openai_query(
                apikey=prompt.get("apikey"),
                model=prompt.get("model"),
                query=query,
                content=nlpdata.content,
                format=prompt.get("format", "text"),
            ).dict()

        return Result(name=self.name, version=self.version, result=res)
