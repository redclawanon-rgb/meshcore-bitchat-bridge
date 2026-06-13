import unittest

from tools.bridge_frame_codec import BridgeFrame, BridgeFrameError, encode_frame
from tools.bridge_frame_codec.meshcore_companion import (
    CMD_SEND_CHANNEL_DATA,
    DATA_TYPE_DEV,
    FLOOD_PATH,
    RESP_CODE_CHANNEL_DATA_RECV,
    build_channel_data_command,
    parse_channel_data_recv,
)


class MeshCoreCompanionTests(unittest.TestCase):
    def sample_bridge_payload(self):
        return encode_frame(
            BridgeFrame(
                flags=0,
                msg_type=0x02,
                bridge_id=1,
                message_id=2,
                fragment_index=0,
                fragment_count=1,
                payload=b"hello",
            )
        )

    def test_build_flood_channel_data_command(self):
        bridge_payload = self.sample_bridge_payload()
        command = build_channel_data_command(bridge_payload, channel_index=1)
        self.assertEqual(command[0], CMD_SEND_CHANNEL_DATA)
        self.assertEqual(command[1], 1)
        self.assertEqual(command[2], FLOOD_PATH)
        self.assertEqual(command[3:5], DATA_TYPE_DEV.to_bytes(2, "little"))
        self.assertEqual(command[5:], bridge_payload)

    def test_build_direct_path_channel_data_command(self):
        bridge_payload = b"abc"
        command = build_channel_data_command(
            bridge_payload,
            channel_index=2,
            data_type=0xFF01,
            path=b"\x10\x20",
        )
        self.assertEqual(command.hex(), "3e0202102001ff616263")

    def test_rejects_reserved_data_type(self):
        with self.assertRaisesRegex(BridgeFrameError, "reserved"):
            build_channel_data_command(b"abc", channel_index=1, data_type=0)

    def test_rejects_bad_channel(self):
        with self.assertRaisesRegex(BridgeFrameError, "channel_index"):
            build_channel_data_command(b"abc", channel_index=8)

    def test_parse_inbound_channel_data_recv(self):
        bridge_payload = self.sample_bridge_payload()
        raw = (
            bytes([RESP_CODE_CHANNEL_DATA_RECV])
            + int(-8).to_bytes(1, "little", signed=True)
            + b"\x00\x00"
            + bytes([1, FLOOD_PATH])
            + DATA_TYPE_DEV.to_bytes(2, "little")
            + bytes([len(bridge_payload)])
            + bridge_payload
        )
        parsed = parse_channel_data_recv(raw)
        self.assertEqual(parsed.snr_scaled, -8)
        self.assertEqual(parsed.snr_db, -2.0)
        self.assertEqual(parsed.channel_index, 1)
        self.assertEqual(parsed.path_len, FLOOD_PATH)
        self.assertEqual(parsed.data_type, DATA_TYPE_DEV)
        self.assertEqual(parsed.payload, bridge_payload)

    def test_parse_rejects_bad_length(self):
        raw = bytes([RESP_CODE_CHANNEL_DATA_RECV, 0, 0, 0, 1, FLOOD_PATH, 0xFF, 0xFF, 3, 1])
        with self.assertRaisesRegex(BridgeFrameError, "length mismatch"):
            parse_channel_data_recv(raw)


if __name__ == "__main__":
    unittest.main()
