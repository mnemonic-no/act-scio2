from typing import Dict, Text

name = "test"
version = 0.1
dependencies = []


async def analyze(text: Text) -> Dict:
    return {"test": text}
