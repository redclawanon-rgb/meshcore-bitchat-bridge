import unittest

from tools.bridge_frame_codec import (
    BITCHAT_MESSAGE_TYPE_MESSAGE,
    BITCHAT_PACKET_VERSION_V1,
    BITCHAT_RECIPIENT_BROADCAST,
    BITCHAT_SIGNATURE_SIZE,
    BitchatPacketFixture,
    BitchatPacketFixtureError,
    decode_raw_v1_packet_fixture,
    make_android_public_message_fixture,
    make_ios_public_message_fixture,
)


class BitchatPacketFixtureTests(unittest.TestCase):
    def test_ios_observed_public_message_shape_has_no_recipient_id(self):
        packet = make_ios_public_message_fixture(
            sender_id=bytes.fromhex("0102030405060708"),
            timestamp_ms=0x0000018F3D2A1B00,
            text="gate4a fixture",
            ttl=7,
        )
        raw = packet.encode_raw_v1()

        self.assertEqual(
            raw.hex(),
            "0102070000018f3d2a1b0000000e01020304050607086761746534612066697874757265",
        )
        decoded = decode_raw_v1_packet_fixture(raw)
        self.assertEqual(decoded.version, BITCHAT_PACKET_VERSION_V1)
        self.assertEqual(decoded.packet_type, BITCHAT_MESSAGE_TYPE_MESSAGE)
        self.assertEqual(decoded.ttl, 7)
        self.assertEqual(decoded.timestamp_ms, 0x0000018F3D2A1B00)
        self.assertEqual(decoded.sender_id, bytes.fromhex("0102030405060708"))
        self.assertIsNone(decoded.recipient_id)
        self.assertEqual(decoded.public_text, "gate4a fixture")
        self.assertIsNone(decoded.signature)

    def test_android_observed_public_message_shape_uses_broadcast_recipient_id(self):
        packet = make_android_public_message_fixture(
            sender_id=bytes.fromhex("0102030405060708"),
            timestamp_ms=0x0000018F3D2A1B00,
            text="gate4a fixture",
            ttl=7,
        )
        raw = packet.encode_raw_v1()

        self.assertEqual(
            raw.hex(),
            "0102070000018f3d2a1b0001000e0102030405060708ffffffffffffffff6761746534612066697874757265",
        )
        decoded = decode_raw_v1_packet_fixture(raw)
        self.assertEqual(decoded.recipient_id, BITCHAT_RECIPIENT_BROADCAST)
        self.assertTrue(decoded.has_broadcast_recipient)
        self.assertEqual(decoded.public_text, "gate4a fixture")

    def test_signature_present_fixture_checks_length_and_preserves_bytes_without_crypto_claim(self):
        signature = bytes(range(BITCHAT_SIGNATURE_SIZE))
        packet = BitchatPacketFixture(
            version=BITCHAT_PACKET_VERSION_V1,
            packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            ttl=7,
            timestamp_ms=0x0000018F3D2A1B00,
            sender_id=bytes.fromhex("0102030405060708"),
            payload=b"gate4a fixture",
            signature=signature,
        )
        raw = packet.encode_raw_v1()

        self.assertEqual(
            raw.hex(),
            "0102070000018f3d2a1b0002000e01020304050607086761746534612066697874757265"
            "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
            "202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f",
        )
        decoded = decode_raw_v1_packet_fixture(raw)
        self.assertEqual(decoded.signature, signature)
        self.assertEqual(decoded.public_text, "gate4a fixture")

        with self.assertRaisesRegex(BitchatPacketFixtureError, "signature must be exactly 64 bytes"):
            BitchatPacketFixture(
                version=BITCHAT_PACKET_VERSION_V1,
                packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
                ttl=7,
                timestamp_ms=0x0000018F3D2A1B00,
                sender_id=bytes.fromhex("0102030405060708"),
                payload=b"gate4a fixture",
                signature=b"too short",
            ).encode_raw_v1()

    def test_rejects_out_of_scope_compressed_and_route_flags(self):
        raw = bytearray(
            make_ios_public_message_fixture(
                sender_id=bytes.fromhex("0102030405060708"),
                timestamp_ms=0x0000018F3D2A1B00,
                text="gate4a fixture",
            ).encode_raw_v1()
        )
        raw[11] = 0x04
        with self.assertRaisesRegex(BitchatPacketFixtureError, "compressed packets are outside fixture scope"):
            decode_raw_v1_packet_fixture(bytes(raw))

        raw[11] = 0x08
        with self.assertRaisesRegex(BitchatPacketFixtureError, "route packets are outside v1 fixture scope"):
            decode_raw_v1_packet_fixture(bytes(raw))


if __name__ == "__main__":
    unittest.main()
