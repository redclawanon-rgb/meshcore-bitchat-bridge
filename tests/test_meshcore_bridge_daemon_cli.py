import json
import unittest
from contextlib import redirect_stdout
import io

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
        self.assertEqual(payload["events"][0]["kind"], "daemon_plan")

    def test_requires_named_port_mapping(self):
        parser = meshcore_bridge_daemon.build_parser()
        args = parser.parse_args(["--port", "COM5"])
        with self.assertRaisesRegex(ValueError, "expected NAME=DEVICE"):
            meshcore_bridge_daemon.run(args)


if __name__ == "__main__":
    unittest.main()
