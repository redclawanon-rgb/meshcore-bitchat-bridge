import unittest

from tools.bridge_frame_codec import (
    BITCHAT_MESSAGE_TYPE_MESSAGE,
    BITCHAT_PACKET_VERSION_V2,
    BitchatPacketFixture,
    FakeBitchatTextCarrier,
    LocalFixtureBitchatAppAdapter,
    make_android_public_message_fixture,
    make_fragment_packet_fixture,
)


class BitchatAppAdapterTests(unittest.TestCase):
    def test_raw_public_message_bytes_emit_semantic_event_once(self):
        carrier = FakeBitchatTextCarrier()
        adapter = LocalFixtureBitchatAppAdapter(carrier=carrier)
        packet = make_android_public_message_fixture(
            sender_id=bytes.fromhex("0102030405060708"),
            timestamp_ms=0x0000018F3D2A1B00,
            text="hello from app adapter",
        )

        events = adapter.ingest_packet_bytes(packet.encode_raw_v1())
        duplicate_events = adapter.ingest_packet_bytes(packet.encode_raw_v1())

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].text, "hello from app adapter")
        self.assertEqual(events[0].sender_id, bytes.fromhex("0102030405060708"))
        self.assertEqual(events[0].timestamp_ms, 0x0000018F3D2A1B00)
        self.assertEqual(events[0].source, "fixture")
        self.assertEqual(duplicate_events, [])

    def test_publish_bridge_text_delegates_to_existing_semantic_carrier(self):
        carrier = FakeBitchatTextCarrier()
        adapter = LocalFixtureBitchatAppAdapter(carrier=carrier)

        adapter.publish_bridge_text("meshcore delivered text", from_bridge_id=9, message_id=123)

        self.assertEqual(len(carrier.published_texts), 1)
        self.assertEqual(carrier.published_texts[0].text, "meshcore delivered text")
        self.assertEqual(carrier.published_texts[0].from_bridge_id, 9)
        self.assertEqual(carrier.published_texts[0].message_id, 123)

    def test_routed_fragments_reassemble_before_public_text_event(self):
        carrier = FakeBitchatTextCarrier()
        adapter = LocalFixtureBitchatAppAdapter(carrier=carrier)
        original = BitchatPacketFixture(
            version=BITCHAT_PACKET_VERSION_V2,
            packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            ttl=5,
            timestamp_ms=0x0000018F3D2A1B00,
            sender_id=bytes.fromhex("0102030405060708"),
            recipient_id=bytes.fromhex("1112131415161718"),
            route=(bytes.fromhex("2122232425262728"),),
            payload=b"fragmented app adapter text",
        )
        original_raw = original.encode_raw_v1()
        first = original_raw[:20]
        second = original_raw[20:]
        fragment_id = bytes.fromhex("a0a1a2a3a4a5a6a7")
        frag0 = make_fragment_packet_fixture(
            original=original,
            fragment_id=fragment_id,
            index=0,
            total=2,
            fragment_data=first,
        )
        frag1 = make_fragment_packet_fixture(
            original=original,
            fragment_id=fragment_id,
            index=1,
            total=2,
            fragment_data=second,
        )

        self.assertEqual(adapter.ingest_packet_bytes(frag1.encode_raw_v1()), [])
        events = adapter.ingest_packet_bytes(frag0.encode_raw_v1())

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].text, "fragmented app adapter text")
        self.assertEqual(events[0].route, (bytes.fromhex("2122232425262728"),))
        self.assertEqual(events[0].sender_id, bytes.fromhex("0102030405060708"))

    def test_exact_duplicate_fragment_is_ignored_until_complete(self):
        carrier = FakeBitchatTextCarrier()
        adapter = LocalFixtureBitchatAppAdapter(carrier=carrier)
        original = make_android_public_message_fixture(
            sender_id=bytes.fromhex("0102030405060708"),
            timestamp_ms=0x0000018F3D2A1B00,
            text="dedupe fragmented text",
        )
        raw = original.encode_raw_v1()
        fragment_id = b"DUPEDUPE"
        frag0 = make_fragment_packet_fixture(
            original=original,
            fragment_id=fragment_id,
            index=0,
            total=2,
            fragment_data=raw[:12],
        )
        frag1 = make_fragment_packet_fixture(
            original=original,
            fragment_id=fragment_id,
            index=1,
            total=2,
            fragment_data=raw[12:],
        )

        self.assertEqual(adapter.ingest_packet_bytes(frag0.encode_raw_v1()), [])
        self.assertEqual(adapter.ingest_packet_bytes(frag0.encode_raw_v1()), [])
        events = adapter.ingest_packet_bytes(frag1.encode_raw_v1())

        self.assertEqual([event.text for event in events], ["dedupe fragmented text"])


if __name__ == "__main__":
    unittest.main()
