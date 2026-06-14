import io
import json
import unittest
from contextlib import redirect_stdout

from tools import bridge_sim


class BridgeSimCliTests(unittest.TestCase):
    def run_cli_json(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = bridge_sim.main(argv)
        self.assertEqual(code, 0)
        return json.loads(buf.getvalue())

    def test_default_bidirectional_demo(self):
        payload = self.run_cli_json([])

        self.assertEqual(payload["type"], "meshcore_bitchat_bridge_sim_v0")
        self.assertEqual(payload["mode"], "no-hardware")
        self.assertEqual(len(payload["exchanges"]), 2)
        self.assertEqual(payload["exchanges"][0]["from"], "alice")
        self.assertEqual(payload["exchanges"][0]["to"], "bob")
        self.assertEqual(payload["exchanges"][0]["delivered_count"], 1)
        self.assertEqual(payload["exchanges"][1]["from"], "bob")
        self.assertEqual(payload["exchanges"][1]["to"], "alice")
        self.assertEqual(payload["exchanges"][1]["delivered_count"], 1)
        self.assertEqual(payload["inbox"]["alice"], ["ack from bob over simulated MeshCore"])
        self.assertEqual(payload["inbox"]["bob"], ["hello from alice over simulated MeshCore"])

    def test_one_way_long_message_reports_multiple_commands(self):
        text = "x" * 400
        payload = self.run_cli_json(["--one-way", "--alice-text", text])

        self.assertEqual(len(payload["exchanges"]), 1)
        exchange = payload["exchanges"][0]
        self.assertGreater(exchange["command_count"], 1)
        self.assertEqual(exchange["command_count"], exchange["notification_count"])
        self.assertEqual(exchange["delivered_count"], 1)
        self.assertEqual(exchange["delivered"][0]["text"], text)
        self.assertEqual(payload["inbox"]["bob"], [text])


if __name__ == "__main__":
    unittest.main()
