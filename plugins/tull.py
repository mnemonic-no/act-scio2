from typing import Dict, Text, DoesNotExist

name = "test"
info = "test info"
version = 0.1
dependencies = []


async def analyze(text: Text) -> Dict:
    return {"test": text}
