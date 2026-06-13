import contextlib
import io
import json
import unittest

from tools.bridge_cli import main


class BridgeCliTests(unittest.TestCase):
    def run_cli_json(self, argv):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(argv)
        self.assertEqual(code, 0)
        return json.loads(stdout.getvalue())

    def test_encode_text_outputs_frame_json(self):
        data = self.run_cli_json([
            "encode-text",
            "--bridge-id",
            "0x1",
            "--message-id",
            "0x2",
            "hello",
        ])
        self.assertEqual(data["type"], "bridge_text_frames_v0")
        self.assertEqual(data["frame_count"], 1)
        self.assertEqual(data["frames"][0]["bridge_id"], "0x00000001")
        self.assertEqual(data["frames"][0]["message_id"], "0x0000000000000002")
        self.assertIsInstance(data["frames"][0]["encoded_hex"], str)

    def test_encode_then_decode_text(self):
        encoded = self.run_cli_json([
            "encode-text",
            "--bridge-id",
            "0xaabbccdd",
            "--message-id",
            "0x0102030405060708",
            "hello 🛰️ mesh",
        ])
        frame_hex = [frame["encoded_hex"] for frame in encoded["frames"]]
        decoded = self.run_cli_json(["decode-frames", *frame_hex])
        self.assertEqual(decoded["type"], "bridge_text_v0")
        self.assertEqual(decoded["bridge_id"], "0xaabbccdd")
        self.assertEqual(decoded["message_id"], "0x0102030405060708")
        self.assertEqual(decoded["text"], "hello 🛰️ mesh")

    def test_multiframe_decode(self):
        text = "x" * 200
        encoded = self.run_cli_json([
            "encode-text",
            "--bridge-id",
            "1",
            "--message-id",
            "2",
            text,
        ])
        self.assertEqual(encoded["frame_count"], 2)
        decoded = self.run_cli_json(
            ["decode-frames", *[frame["encoded_hex"] for frame in reversed(encoded["frames"])] ]
        )
        self.assertEqual(decoded["text"], text)


if __name__ == "__main__":
    unittest.main()
