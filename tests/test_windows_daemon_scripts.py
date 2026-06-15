import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
START_SCRIPT = ROOT / "scripts" / "windows" / "Start-MeshCoreBridgeDaemon.ps1"
INSTALL_SCRIPT = ROOT / "scripts" / "windows" / "Install-MeshCoreBridgeScheduledTask.ps1"
DOC = ROOT / "docs" / "windows-daemon-scheduled-task.md"


class WindowsDaemonScriptTests(unittest.TestCase):
    def test_launcher_preserves_no_open_default_and_live_gate(self):
        text = START_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("[switch]$OpenRealPorts", text)
        self.assertIn('"dry-run-no-ports-opened"', text)
        self.assertIn('"--open-real-ports"', text)
        self.assertIn('"--event-log", $EventLog', text)
        self.assertIn('"--state-file", $StateFile', text)
        self.assertIn('"--port", "pocket1=$Pocket1Port"', text)
        self.assertIn('"--port", "pocket2=$Pocket2Port"', text)

    def test_scheduled_task_installer_requires_explicit_live_enable(self):
        text = INSTALL_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("[switch]$EnableRealPorts", text)
        self.assertIn("if ($EnableRealPorts)", text)
        self.assertIn('"-OpenRealPorts"', text)
        self.assertIn("[string[]]$InjectText = @()", text)
        self.assertIn('"-InjectText", (Quote-TaskArg $item)', text)
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn", text)
        self.assertIn("Register-ScheduledTask", text)
        self.assertIn("-RestartCount 999", text)
        self.assertIn("-MultipleInstances IgnoreNew", text)

    def test_docs_record_ports_paths_and_non_claims(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("pocket1=COM5", text)
        self.assertIn("pocket2=COM8", text)
        self.assertIn("%LOCALAPPDATA%\\MeshCoreBitchatBridge", text)
        self.assertIn("does not add the real bitchat/mobile side", text)
        self.assertIn("-EnableRealPorts -StartNow", text)


if __name__ == "__main__":
    unittest.main()
