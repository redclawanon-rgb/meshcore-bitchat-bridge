import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from tools import no_hardware_smoke


class NoHardwareSmokeCliTests(unittest.TestCase):
    def run_cli_json(self, argv=None):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = no_hardware_smoke.main([] if argv is None else argv)
        self.assertEqual(code, 0)
        return json.loads(buf.getvalue())

    def test_smoke_runs_documented_demo_clis_and_summarizes_stable_fields(self):
        payload = self.run_cli_json()

        self.assertEqual(
            payload["type"], "meshcore_bitchat_bridge_no_hardware_smoke_v0"
        )
        self.assertEqual(payload["mode"], "no-hardware")
        self.assertEqual(
            payload["safety"],
            {
                "opens_ble": False,
                "opens_serial": False,
                "opens_network": False,
                "stock_bitchat_compatibility": "not-claimed",
                "uses_real_hardware": False,
            },
        )
        self.assertEqual(payload["demo_count"], 3)
        self.assertEqual(
            [demo["name"] for demo in payload["demos"]],
            ["bridge_sim_one_way", "bridge_serial_dry_run", "bridge_pump_demo"],
        )

        sim = payload["demos"][0]
        self.assertEqual(
            sim["command"],
            [
                "python3",
                "tools/bridge_sim.py",
                "--one-way",
                "--alice-text",
                "smoke test over simulated MeshCore",
            ],
        )
        self.assertEqual(sim["stable_fields"]["type"], "meshcore_bitchat_bridge_sim_v0")
        self.assertEqual(sim["stable_fields"]["mode"], "no-hardware")
        self.assertEqual(sim["stable_fields"]["exchange_count"], 1)
        self.assertEqual(
            sim["stable_fields"]["first_exchange"],
            {
                "from": "alice",
                "to": "bob",
                "command_count": 1,
                "notification_count": 1,
                "delivered_count": 1,
                "delivered_text": "smoke test over simulated MeshCore",
            },
        )
        self.assertEqual(sim["stable_fields"]["inbox"]["alice_count"], 0)
        self.assertEqual(sim["stable_fields"]["inbox"]["bob_count"], 1)

        serial = payload["demos"][1]
        self.assertEqual(
            serial["command"],
            [
                "python3",
                "tools/bridge_serial.py",
                "--port",
                "/dev/ttyUSB0",
                "serial smoke",
            ],
        )
        self.assertEqual(
            serial["stable_fields"]["type"],
            "meshcore_bitchat_bridge_serial_dry_run_v0",
        )
        self.assertEqual(serial["stable_fields"]["mode"], "dry-run-no-port-opened")
        self.assertEqual(serial["stable_fields"]["port"], "/dev/ttyUSB0")
        self.assertEqual(serial["stable_fields"]["packet_count"], 1)
        self.assertEqual(
            serial["stable_fields"]["first_packet"]["serial_tx_hex_prefix"], "3c"
        )
        self.assertEqual(
            serial["stable_fields"]["first_packet"]["companion_command_hex_prefix"],
            "3e",
        )

        pump = payload["demos"][2]
        self.assertEqual(pump["command"], ["python3", "tools/bridge_pump_demo.py"])
        self.assertEqual(
            pump["stable_fields"]["type"], "meshcore_bitchat_bridge_pump_demo_v0"
        )
        self.assertEqual(pump["stable_fields"]["mode"], "no-hardware")
        self.assertEqual(
            pump["stable_fields"]["safety"],
            {
                "opens_ble": False,
                "opens_serial": False,
                "stock_bitchat_compatibility": "not-claimed",
                "uses_fake_bitchat_text_carrier": True,
                "uses_fake_meshcore_transport": True,
            },
        )
        self.assertEqual(
            pump["stable_fields"]["pump_counts"],
            {
                "bitchat_texts_forwarded": 1,
                "meshcore_commands_sent": 1,
                "meshcore_notifications_delivered": 1,
                "meshcore_texts_published": 1,
            },
        )
        self.assertEqual(pump["stable_fields"]["carrier"]["published_count"], 1)
        self.assertEqual(pump["stable_fields"]["receiver"]["delivered_count"], 1)

    def test_rejects_unexpected_args(self):
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(no_hardware_smoke.main(["--unexpected"]), 2)
        self.assertIn("usage: no_hardware_smoke.py", err.getvalue())


if __name__ == "__main__":
    unittest.main()
