import json
from pathlib import Path
import unittest

from tools.bridge_frame_codec import (
    BridgeFrame,
    BridgeFrameError,
    FIXED_OVERHEAD,
    MAX_CARRIER_PAYLOAD,
    MAX_FRAME_PAYLOAD,
    crc16_xmodem,
    decode_frame,
    encode_frame,
    fragment_payload,
    reassemble_fragments,
)


class BridgeFrameCodecTests(unittest.TestCase):
    def test_crc16_xmodem_known_check_value(self):
        self.assertEqual(crc16_xmodem(b"123456789"), 0x31C3)

    def test_encode_decode_text_fragment(self):
        frame = BridgeFrame(
            flags=0x01,
            msg_type=0x02,
            bridge_id=0xA1B2C3D4,
            message_id=0x0102030405060708,
            fragment_index=0,
            fragment_count=1,
            payload=b"hello",
        )
        raw = encode_frame(frame)
        self.assertEqual(len(raw), FIXED_OVERHEAD + 5)
        self.assertEqual(decode_frame(raw), frame)

    def test_frame_fits_meshcore_companion_limit(self):
        frame = BridgeFrame(
            flags=0,
            msg_type=0x02,
            bridge_id=1,
            message_id=2,
            fragment_index=0,
            fragment_count=1,
            payload=b"x" * MAX_FRAME_PAYLOAD,
        )
        self.assertEqual(len(encode_frame(frame)), MAX_CARRIER_PAYLOAD)

    def test_json_vector_matches_codec(self):
        vector_path = Path(__file__).parent / "vectors" / "bridge-frame-v0.json"
        data = json.loads(vector_path.read_text())
        vector = data["vectors"][0]
        fields = vector["fields"]
        frame = BridgeFrame(
            flags=int(fields["flags"], 16),
            msg_type=int(fields["msg_type"], 16),
            bridge_id=int(fields["bridge_id"], 16),
            message_id=int(fields["message_id"], 16),
            fragment_index=fields["fragment_index"],
            fragment_count=fields["fragment_count"],
            payload=bytes.fromhex(fields["payload_hex"]),
        )
        raw = encode_frame(frame)
        self.assertEqual(raw.hex(), vector["encoded_hex"])
        self.assertEqual(len(raw), vector["encoded_len"])
        self.assertEqual(decode_frame(raw), frame)

    def test_rejects_bad_crc(self):
        frame = BridgeFrame(
            flags=0,
            msg_type=0x02,
            bridge_id=1,
            message_id=2,
            fragment_index=0,
            fragment_count=1,
            payload=b"hello",
        )
        raw = bytearray(encode_frame(frame))
        raw[-1] ^= 0xFF
        with self.assertRaisesRegex(BridgeFrameError, "crc mismatch"):
            decode_frame(bytes(raw))

    def test_rejects_oversize_payload(self):
        with self.assertRaisesRegex(BridgeFrameError, "payload too large"):
            encode_frame(
                BridgeFrame(
                    flags=0,
                    msg_type=0x02,
                    bridge_id=1,
                    message_id=2,
                    fragment_index=0,
                    fragment_count=1,
                    payload=b"x" * (MAX_FRAME_PAYLOAD + 1),
                )
            )

    def test_fragment_and_reassemble_out_of_order_with_duplicate(self):
        payload = b"a" * MAX_FRAME_PAYLOAD + b"b" * 10
        frames = fragment_payload(
            payload,
            flags=0x01,
            msg_type=0x02,
            bridge_id=0xAA55AA55,
            message_id=0x123456789ABCDEF0,
        )
        self.assertEqual(len(frames), 2)
        out_of_order = [frames[1], frames[0], frames[1]]
        self.assertEqual(reassemble_fragments(out_of_order), payload)

    def test_reassembly_rejects_missing_fragment(self):
        payload = b"a" * MAX_FRAME_PAYLOAD + b"b"
        frames = fragment_payload(
            payload,
            flags=0,
            msg_type=0x02,
            bridge_id=1,
            message_id=2,
        )
        with self.assertRaisesRegex(BridgeFrameError, "missing fragments"):
            reassemble_fragments(frames[:1])

    def test_reassembly_rejects_conflicting_duplicate(self):
        frame_a = BridgeFrame(0, 0x02, 1, 2, 0, 1, b"hello")
        frame_b = BridgeFrame(0, 0x02, 1, 2, 0, 1, b"HELLO")
        with self.assertRaisesRegex(BridgeFrameError, "conflicting duplicate"):
            reassemble_fragments([frame_a, frame_b])


if __name__ == "__main__":
    unittest.main()
