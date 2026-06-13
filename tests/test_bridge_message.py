import unittest

from tools.bridge_frame_codec import BridgeFrame, BridgeFrameError, MAX_FRAME_PAYLOAD
from tools.bridge_frame_codec.bridge_frame import MSG_ACK, MSG_TEXT_FRAGMENT
from tools.bridge_frame_codec.message import frames_to_text, max_text_bytes, text_to_frames


class BridgeMessageTests(unittest.TestCase):
    def test_empty_text_roundtrip(self):
        frames = text_to_frames("", bridge_id=1, message_id=2)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].payload, b"")
        self.assertEqual(frames_to_text(frames), "")

    def test_ascii_text_roundtrip(self):
        frames = text_to_frames("hello mesh", bridge_id=1, message_id=2, flags=0x01)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].msg_type, MSG_TEXT_FRAGMENT)
        self.assertEqual(frames[0].flags, 0x01)
        self.assertEqual(frames_to_text(frames), "hello mesh")

    def test_multibyte_utf8_can_span_fragments(self):
        # 140 ASCII bytes plus a 4-byte emoji forces the emoji across the
        # 141-byte fragment boundary if splitting by raw bytes.
        text = "a" * (MAX_FRAME_PAYLOAD - 1) + "🛰️" + "b" * 3
        frames = text_to_frames(text, bridge_id=0xAA, message_id=0xBB)
        self.assertGreater(len(frames), 1)
        self.assertEqual(frames_to_text(list(reversed(frames))), text)

    def test_message_too_large_for_255_fragments(self):
        oversized = "x" * (max_text_bytes() + 1)
        with self.assertRaisesRegex(BridgeFrameError, "too many fragments"):
            text_to_frames(oversized, bridge_id=1, message_id=2)

    def test_mixed_message_ids_rejected(self):
        frames_a = text_to_frames("hello", bridge_id=1, message_id=2)
        frames_b = text_to_frames("world", bridge_id=1, message_id=3)
        with self.assertRaisesRegex(BridgeFrameError, "mixed fragment keys"):
            frames_to_text([frames_a[0], frames_b[0]])

    def test_non_text_frame_rejected(self):
        frame = BridgeFrame(
            flags=0,
            msg_type=MSG_ACK,
            bridge_id=1,
            message_id=2,
            fragment_index=0,
            fragment_count=1,
            payload=b"ack",
        )
        with self.assertRaisesRegex(BridgeFrameError, "unexpected msg_type"):
            frames_to_text([frame])

    def test_invalid_utf8_rejected(self):
        frame = BridgeFrame(
            flags=0,
            msg_type=MSG_TEXT_FRAGMENT,
            bridge_id=1,
            message_id=2,
            fragment_index=0,
            fragment_count=1,
            payload=b"\xff",
        )
        with self.assertRaisesRegex(BridgeFrameError, "invalid UTF-8"):
            frames_to_text([frame])


if __name__ == "__main__":
    unittest.main()
