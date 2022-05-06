import os

import addict
import pytest

from act.scio.plugins import mitre_attack

TEST_TEXT = """
Technical Analysis of Operation Diànxùn18REPORTTa c t i c
TechniqueObservableIOCsResource DevelopmentAcquire Infrastructure: Domains
(T1583.001)Attackers purchased domains to develop their phishing attack.
“flach.cn”“careerhuawei.net”Develop capabilities: Malware (T1587.001)Attackers
built malicious components to conduct their attack. Fake FlashUtility
DownloaderAddTaskPlanDllVersion.dllObtain capabilities: Tool
(T1588.002)Attackers acquired red teaming tools to conduct their attack.Cobalt
Strike Initial AccessSpear phishing Link (T1566.002)ExecutionUser Execution
(T1204.001)Users are redirected to the Fake Flash website to download the first
stage.Persistence Scheduled Task/Job: Scheduled Task (T1053.005)The DotNet
Utility creates a scheduled task that will run cmd.exe /c with the previous
payload downloaded and create registry key.“SOFTWARE\\Microsoft\\Windows
NT\\CurrentVersion\\AppCompatFlags\\TelemetryController\\Levint”Create or
Modify System Process: Windows Service (T1543.003)The DotNet utility can add a
WMI backdoor by creating a permanent filter in order to stay persistent in the
infected machine.Defense EvasionProcess Injection (T1055)The DotNet utility has
the possibility to inject shellcode into the clipboard.Command And Control
Application Layer Protocol: Web Proto

G1234
G4321.
S1234,S4321.
TA1234.
TA4321
"""


@pytest.mark.asyncio  # type: ignore
async def test_sectors() -> None:
    """test for plugins"""

    nlpdata = addict.Dict()
    plugin = mitre_attack.Plugin()
    plugin.configdir = os.path.join(
        os.path.dirname(__file__), "../act/scio/etc/plugins"
    )

    nlpdata.content = TEST_TEXT

    res = await plugin.analyze(nlpdata)

    assert len(res.result.Groups) == 2
    assert "G4321" in res.result.Groups
    assert "G1234" in res.result.Groups
    assert len(res.result.Tactics) == 2
    assert "TA4321" in res.result.Tactics
    assert "TA1234" in res.result.Tactics
    assert "T1055" in res.result.Techniques
    assert "T1055" not in res.result.SubTechniques
    assert len(res.result.SubTechniques) == 7
    assert "T1583.001" in res.result.SubTechniques
    assert "T1587.001" in res.result.SubTechniques
    assert "T1588.002" in res.result.SubTechniques
    assert "T1566.002" in res.result.SubTechniques
    assert "T1204.001" in res.result.SubTechniques
    assert "T1053.005" in res.result.SubTechniques
    assert len(res.result.Software) == 2
    assert "S1234" in res.result.Software
    assert "S4321" in res.result.Software
