import json
import unittest
from contextlib import redirect_stdout
import io

from tools import live_lora_smoke


class LiveLoraSmokeCliTests(unittest.TestCase):
    def test_default_is_no_open_dry_run(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = live_lora_smoke.main([
                "--tx-port",
                "COM5",
                "--rx-port",
                "COM8",
                "hello lora",
            ])
        payload = json.loads(buf.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"], "dry-run-no-ports-opened")
        self.assertEqual(payload["tx_port"], "COM5")
        self.assertEqual(payload["rx_port"], "COM8")
        self.assertEqual(payload["command_count"], 1)
        self.assertEqual(payload["delivered"], [])
        self.assertEqual(payload["raw_rx_hex_chunks"], [])
    def test_polls_after_unknown_sync_next_response(self):
        self.assertTrue(live_lora_smoke._should_poll_sync_next_after_frame("unknown_0x08"))
        self.assertTrue(live_lora_smoke._should_poll_sync_next_after_frame("channel_data_recv"))
        self.assertFalse(live_lora_smoke._should_poll_sync_next_after_frame("no_more_messages"))


if __name__ == "__main__":
    unittest.main()
