import unittest

from tools.bridge_frame_codec import (
    BITCHAT_MESSAGE_TYPE_FRAGMENT,
    BITCHAT_MESSAGE_TYPE_MESSAGE,
    BITCHAT_PACKET_VERSION_V1,
    BITCHAT_PACKET_VERSION_V2,
    BITCHAT_RECIPIENT_BROADCAST,
    BitchatFragmentPayloadFixture,
    BitchatPacketFixture,
    BitchatPacketFixtureError,
    compute_packet_id_hex_fixture,
    decode_fragment_payload_fixture,
    decode_raw_v1_packet_fixture,
    decode_wire_v1_packet_fixture,
    make_fragment_packet_fixture,
    reassemble_fragment_payload_fixtures,
)


class BitchatV2RouteFragmentFixtureTests(unittest.TestCase):
    def test_v2_routed_packet_raw_shape_uses_uint32_length_and_route_hops(self):
        packet = BitchatPacketFixture(
            version=BITCHAT_PACKET_VERSION_V2,
            packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            ttl=5,
            timestamp_ms=0x0000018F3D2A1B00,
            sender_id=bytes.fromhex("0102030405060708"),
            recipient_id=bytes.fromhex("1112131415161718"),
            route=(
                bytes.fromhex("2122232425262728"),
                bytes.fromhex("3132333435363738"),
            ),
            payload=b"route fixture",
        )

        raw = packet.encode_raw_v1()
        self.assertEqual(
            raw.hex(),
            "0202050000018f3d2a1b00090000000d0102030405060708"
            "11121314151617180221222324252627283132333435363738"
            "726f7574652066697874757265",
        )

        decoded = decode_raw_v1_packet_fixture(raw)
        self.assertEqual(decoded.version, BITCHAT_PACKET_VERSION_V2)
        self.assertEqual(decoded.recipient_id, bytes.fromhex("1112131415161718"))
        self.assertEqual(
            decoded.route,
            (bytes.fromhex("2122232425262728"), bytes.fromhex("3132333435363738")),
        )
        self.assertEqual(decoded.payload, b"route fixture")

    def test_v1_route_is_rejected_but_v2_route_padding_roundtrips(self):
        with self.assertRaisesRegex(BitchatPacketFixtureError, "route fixtures require packet version 2"):
            BitchatPacketFixture(
                version=BITCHAT_PACKET_VERSION_V1,
                packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
                ttl=5,
                timestamp_ms=0,
                sender_id=bytes.fromhex("0102030405060708"),
                route=(bytes.fromhex("2122232425262728"),),
                payload=b"bad route",
            ).encode_raw_v1()

        packet = BitchatPacketFixture(
            version=BITCHAT_PACKET_VERSION_V2,
            packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            ttl=5,
            timestamp_ms=0x0000018F3D2A1B00,
            sender_id=bytes.fromhex("0102030405060708"),
            recipient_id=BITCHAT_RECIPIENT_BROADCAST,
            route=(bytes.fromhex("2122232425262728"),),
            payload=b"padded route",
        )
        decoded = decode_wire_v1_packet_fixture(packet.encode_wire_v1())
        self.assertEqual(decoded.version, BITCHAT_PACKET_VERSION_V2)
        self.assertEqual(decoded.route, (bytes.fromhex("2122232425262728"),))
        self.assertEqual(decoded.payload, b"padded route")

    def test_fragment_payload_shape_and_packet_id_are_deterministic(self):
        fragment = BitchatFragmentPayloadFixture(
            fragment_id=bytes.fromhex("a0a1a2a3a4a5a6a7"),
            index=1,
            total=3,
            original_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            data=b"chunk-two",
        )

        encoded = fragment.encode()
        self.assertEqual(encoded.hex(), "a0a1a2a3a4a5a6a700010003026368756e6b2d74776f")
        decoded = decode_fragment_payload_fixture(encoded)
        self.assertEqual(decoded, fragment)

        packet = BitchatPacketFixture(
            version=BITCHAT_PACKET_VERSION_V1,
            packet_type=BITCHAT_MESSAGE_TYPE_FRAGMENT,
            ttl=7,
            timestamp_ms=0x0000018F3D2A1B00,
            sender_id=bytes.fromhex("0102030405060708"),
            payload=encoded,
        )
        self.assertEqual(compute_packet_id_hex_fixture(packet), "88a8a59f0e1c1091d025b3427b94188f")

    def test_routed_fragment_packet_preserves_route_and_reassembles_original_bytes(self):
        original = BitchatPacketFixture(
            version=BITCHAT_PACKET_VERSION_V2,
            packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            ttl=5,
            timestamp_ms=0x0000018F3D2A1B00,
            sender_id=bytes.fromhex("0102030405060708"),
            recipient_id=bytes.fromhex("1112131415161718"),
            route=(bytes.fromhex("2122232425262728"),),
            payload=b"abcdefghijklmnopqrstuvwxyz",
        )
        original_raw = original.encode_raw_v1()
        first = original_raw[:18]
        second = original_raw[18:]

        frag0_packet = make_fragment_packet_fixture(
            original=original,
            fragment_id=bytes.fromhex("a0a1a2a3a4a5a6a7"),
            index=0,
            total=2,
            fragment_data=first,
        )
        frag1_packet = make_fragment_packet_fixture(
            original=original,
            fragment_id=bytes.fromhex("a0a1a2a3a4a5a6a7"),
            index=1,
            total=2,
            fragment_data=second,
        )

        self.assertEqual(frag0_packet.version, BITCHAT_PACKET_VERSION_V2)
        self.assertEqual(frag0_packet.packet_type, BITCHAT_MESSAGE_TYPE_FRAGMENT)
        self.assertEqual(frag0_packet.route, original.route)
        self.assertIsNone(frag0_packet.signature)

        reassembled = reassemble_fragment_payload_fixtures(
            [
                decode_fragment_payload_fixture(frag1_packet.payload),
                decode_fragment_payload_fixture(frag0_packet.payload),
            ]
        )
        self.assertEqual(reassembled, original_raw)
        decoded_original = decode_raw_v1_packet_fixture(reassembled)
        self.assertEqual(decoded_original.route, original.route)
        self.assertEqual(decoded_original.payload, b"abcdefghijklmnopqrstuvwxyz")

    def test_fragment_reassembly_rejects_missing_and_conflicting_fragments(self):
        frag0 = BitchatFragmentPayloadFixture(
            fragment_id=b"ABCDEFGH",
            index=0,
            total=2,
            original_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            data=b"one",
        )
        frag1 = BitchatFragmentPayloadFixture(
            fragment_id=b"ABCDEFGH",
            index=1,
            total=2,
            original_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            data=b"two",
        )
        frag1_conflict = BitchatFragmentPayloadFixture(
            fragment_id=b"ABCDEFGH",
            index=1,
            total=2,
            original_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            data=b"bad",
        )

        with self.assertRaisesRegex(BitchatPacketFixtureError, "incomplete fragment set"):
            reassemble_fragment_payload_fixtures([frag0])
        with self.assertRaisesRegex(BitchatPacketFixtureError, "conflicting duplicate fragment"):
            reassemble_fragment_payload_fixtures([frag0, frag1, frag1_conflict])
        self.assertEqual(reassemble_fragment_payload_fixtures([frag1, frag0]), b"onetwo")


if __name__ == "__main__":
    unittest.main()
