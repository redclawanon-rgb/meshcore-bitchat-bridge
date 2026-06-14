import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools import meshcore_bridge_daemon


class MeshCoreBridgeDaemonCliTests(unittest.TestCase):
    def test_default_is_no_open_plan(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = meshcore_bridge_daemon.main([
                "--port",
                "pocket1=COM5",
                "--port",
                "pocket2=COM8",
                "--inject-text",
                "pocket1:hello daemon",
                "--duration-seconds",
                "1",
            ])
        payload = json.loads(buf.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"], "dry-run-no-ports-opened")
        self.assertEqual(payload["ports"], {"pocket1": "COM5", "pocket2": "COM8"})
        self.assertEqual(payload["injection_count"], 1)
        self.assertEqual(payload["delivered_count"], 0)
        self.assertEqual(payload["parse_error_count"], 0)
        self.assertEqual(payload["reconnect_count"], 0)
        self.assertEqual(payload["events"][0]["kind"], "daemon_plan")

    def test_dry_run_writes_jsonl_event_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "events.jsonl"
            args = meshcore_bridge_daemon.build_parser().parse_args([
                "--port",
                "pocket1=COM5",
                "--event-log",
                str(log_path),
            ])
            payload = meshcore_bridge_daemon.run(args)
            lines = log_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(payload["event_count"], 1)
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["kind"], "daemon_plan")

    def test_state_file_message_id_overrides_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "daemon-state.json"
            state_path.write_text(json.dumps({"next_message_id": 1234}), encoding="utf-8")
            args = meshcore_bridge_daemon.build_parser().parse_args([
                "--port",
                "pocket1=COM5",
                "--state-file",
                str(state_path),
                "--message-id-start",
                "2",
            ])
            payload = meshcore_bridge_daemon.run(args)

        events = payload["events"]
        self.assertIsInstance(events, list)
        self.assertTrue(events[0]["state_loaded"])  # type: ignore[index]

    def test_requires_named_port_mapping(self):
        parser = meshcore_bridge_daemon.build_parser()
        args = parser.parse_args(["--port", "COM5"])
        with self.assertRaisesRegex(ValueError, "expected NAME=DEVICE"):
            meshcore_bridge_daemon.run(args)


if __name__ == "__main__":
    unittest.main()
