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
        self.assertFalse(payload["relay_stock_text"])
        self.assertEqual(payload["delivered_count"], 0)
        self.assertEqual(payload["parse_error_count"], 0)
        self.assertEqual(payload["reconnect_count"], 0)
        self.assertEqual(payload["relay_sent_count"], 0)
        self.assertEqual(payload["relay_skipped_count"], 0)
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

    def test_polls_after_unknown_sync_next_response(self):
        self.assertTrue(meshcore_bridge_daemon._should_poll_sync_next_after_frame("unknown_0x08"))
        self.assertTrue(meshcore_bridge_daemon._should_poll_sync_next_after_frame("channel_data_recv"))
        self.assertTrue(meshcore_bridge_daemon._should_poll_sync_next_after_frame("contact_msg_recv"))
        self.assertFalse(meshcore_bridge_daemon._should_poll_sync_next_after_frame("path_update"))
        self.assertFalse(meshcore_bridge_daemon._should_poll_sync_next_after_frame("no_more_messages"))

    def test_classifies_stock_meshcore_message_frames(self):
        self.assertEqual(
            meshcore_bridge_daemon._classify_frame(bytes.fromhex("07769b8ca6fe830000824d2f6a546573742066726f6d2033")),
            "contact_msg_recv",
        )
        self.assertEqual(meshcore_bridge_daemon._classify_frame(bytes.fromhex("81769b8ca6")), "path_update")

    def test_parses_stock_meshcore_contact_text_message_from_iphone(self):
        frame = bytes.fromhex("07769b8ca6fe830000824d2f6a546573742066726f6d2033")
        parsed = meshcore_bridge_daemon._parse_meshcore_text_message(frame)

        self.assertEqual(
            parsed,
            {
                "message_scope": "contact",
                "pubkey_prefix": "769b8ca6fe83",
                "path_hash_mode": 0,
                "path_len": 0,
                "txt_type": 0,
                "sender_timestamp": 1781484930,
                "text": "Test from 3",
            },
        )

    def test_parses_stock_meshcore_channel_text_message(self):
        frame = b"\x08\x01\x00\x00" + (12345).to_bytes(4, "little") + b"hello channel"
        parsed = meshcore_bridge_daemon._parse_meshcore_text_message(frame)

        self.assertEqual(
            parsed,
            {
                "message_scope": "channel",
                "channel_idx": 1,
                "path_hash_mode": 0,
                "path_len": 0,
                "txt_type": 0,
                "sender_timestamp": 12345,
                "text": "hello channel",
            },
        )

    def test_stock_text_dedupe_key_collapses_duplicate_receives(self):
        left = meshcore_bridge_daemon._parse_meshcore_text_message(
            bytes.fromhex("07769b8ca6fe830000824d2f6a546573742066726f6d2033")
        )
        self.assertIsNotNone(left)
        right = dict(left or {})

        self.assertEqual(
            meshcore_bridge_daemon._stock_text_dedupe_key(left or {}),
            meshcore_bridge_daemon._stock_text_dedupe_key(right),
        )

    def test_build_stock_channel_text_command(self):
        command = meshcore_bridge_daemon._build_stock_channel_text_command("[relay] hello", 1, timestamp=12345)

        self.assertEqual(command, b"\x03\x00\x01" + (12345).to_bytes(4, "little") + b"[relay] hello")


if __name__ == "__main__":
    unittest.main()
