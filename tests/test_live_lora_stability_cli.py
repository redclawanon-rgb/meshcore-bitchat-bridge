import json
import unittest
from contextlib import redirect_stdout
import io

from tools import live_lora_stability


class LiveLoraStabilityCliTests(unittest.TestCase):
    def test_default_is_no_open_dry_run_with_alternating_attempts(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = live_lora_stability.main([
                "--port-a",
                "COM5",
                "--port-b",
                "COM8",
                "--count",
                "3",
                "--pause-seconds",
                "0",
            ])
        payload = json.loads(buf.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"], "dry-run-no-ports-opened")
        self.assertEqual(payload["count"], 3)
        self.assertEqual(payload["delivered"], 0)
        self.assertEqual(payload["failed"], 3)
        self.assertEqual([a["direction"] for a in payload["attempts"]], ["A_to_B", "B_to_A", "A_to_B"])
        self.assertEqual(payload["parse_error_count"], 0)


if __name__ == "__main__":
    unittest.main()
