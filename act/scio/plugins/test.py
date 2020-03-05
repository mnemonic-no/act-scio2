from typing import Text, List, Dict
import plugin

name = "test"
info = "test info"
version = 0.1
dependencies: List[Text] = []


def analyze(text: Text, prior_result: Dict) -> plugin.Result:
    return plugin.Result(name=name, version=version, result={"test": text})
