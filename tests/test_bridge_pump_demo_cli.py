import io
import json
import unittest
from contextlib import redirect_stdout

from tools import bridge_pump_demo


class BridgePumpDemoCliTests(unittest.TestCase):
    def run_cli_json(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = bridge_pump_demo.main(argv)
        self.assertEqual(code, 0)
        return json.loads(buf.getvalue())

    def test_default_demo_prints_deterministic_no_hardware_summary(self):
        payload = self.run_cli_json([])

        self.assertEqual(payload["type"], "meshcore_bitchat_bridge_pump_demo_v0")
        self.assertEqual(payload["mode"], "no-hardware")
        self.assertEqual(
            payload["safety"],
            {
                "opens_ble": False,
                "opens_serial": False,
                "stock_bitchat_compatibility": "not-claimed",
                "uses_fake_bitchat_text_carrier": True,
                "uses_fake_meshcore_transport": True,
            },
        )
        self.assertEqual(payload["seeded"], {"meshcore_commands": 1, "bitchat_public_texts": 1})
        self.assertEqual(
            payload["pump_counts"],
            {
                "meshcore_notifications_delivered": 1,
                "meshcore_texts_published": 1,
                "bitchat_texts_forwarded": 1,
                "meshcore_commands_sent": 1,
            },
        )
        self.assertEqual(payload["carrier"]["published_count"], 1)
        self.assertEqual(
            payload["carrier"]["published_messages"],
            [
                {
                    "from_bridge_id": "0x000000a1",
                    "message_id": 1,
                    "text": "meshcore public text into fake carrier",
                }
            ],
        )
        self.assertEqual(payload["carrier"]["queued_public_texts_remaining"], 0)
        self.assertEqual(payload["receiver"]["delivered_count"], 1)
        self.assertEqual(
            payload["receiver"]["inbox"],
            [
                {
                    "from_bridge_id": "0x000000b2",
                    "message_id": 1,
                    "text": "fake carrier public text into meshcore",
                }
            ],
        )
        self.assertEqual(
            payload["receiver"]["inbox_texts"],
            ["fake carrier public text into meshcore"],
        )
        self.assertEqual(payload["transport"]["sent_command_count"], 2)
        self.assertEqual(payload["transport"]["queued_notifications_remaining"], 0)

    def test_custom_long_bitchat_text_reports_fragmented_forwarding(self):
        long_text = "carrier " + ("x" * 400)
        payload = self.run_cli_json(
            [
                "--meshcore-text",
                "mesh side",
                "--bitchat-text",
                long_text,
                "--bridge-id",
                "0x22",
            ]
        )

        self.assertEqual(payload["mode"], "no-hardware")
        self.assertEqual(payload["carrier"]["published_messages"][0]["text"], "mesh side")
        self.assertEqual(payload["receiver"]["inbox_texts"], [long_text])
        self.assertEqual(payload["pump_counts"]["bitchat_texts_forwarded"], 1)
        self.assertGreater(payload["pump_counts"]["meshcore_commands_sent"], 1)
        self.assertEqual(
            payload["transport"]["sent_command_count"],
            payload["seeded"]["meshcore_commands"]
            + payload["pump_counts"]["meshcore_commands_sent"],
        )
        self.assertEqual(payload["receiver"]["inbox"][0]["from_bridge_id"], "0x00000022")


if __name__ == "__main__":
    unittest.main()
