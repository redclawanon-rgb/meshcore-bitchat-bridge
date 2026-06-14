import unittest

from tools.bridge_frame_codec import (
    AppAdapterBridgePumpResult,
    BITCHAT_MESSAGE_TYPE_MESSAGE,
    BITCHAT_PACKET_VERSION_V2,
    BitchatPacketFixture,
    FakeBitchatTextCarrier,
    FakeCompanionDatagramTransport,
    LocalFixtureBitchatAppAdapter,
    SimulatedBridgeNode,
    drain_transport_to_node,
    make_android_public_message_fixture,
    make_fragment_packet_fixture,
    pump_app_adapter_bridge_once,
    send_text_over_transport,
)


class BitchatAppAdapterPumpTests(unittest.TestCase):
    def test_meshcore_delivered_text_is_published_through_app_adapter(self):
        mesh_sender = SimulatedBridgeNode(bridge_id=101)
        bridge_node = SimulatedBridgeNode(bridge_id=202)
        transport = FakeCompanionDatagramTransport()
        carrier = FakeBitchatTextCarrier()
        adapter = LocalFixtureBitchatAppAdapter(carrier=carrier)

        commands_sent = send_text_over_transport(
            mesh_sender,
            transport,
            "meshcore to app adapter",
        )
        result = pump_app_adapter_bridge_once(
            mesh_node=bridge_node,
            mesh_transport=transport,
            bitchat_adapter=adapter,
        )

        self.assertEqual(commands_sent, 1)
        self.assertEqual(
            result,
            AppAdapterBridgePumpResult(
                meshcore_notifications_delivered=1,
                meshcore_texts_published_to_app=1,
                bitchat_packets_ingested=0,
                bitchat_public_events_forwarded=0,
                meshcore_commands_sent=0,
            ),
        )
        self.assertEqual(len(carrier.published_texts), 1)
        self.assertEqual(carrier.published_texts[0].text, "meshcore to app adapter")
        self.assertEqual(carrier.published_texts[0].from_bridge_id, 101)
        self.assertEqual(carrier.published_texts[0].message_id, 1)
        self.assertEqual(bridge_node.inbox, [])

    def test_app_adapter_public_packet_event_is_forwarded_to_meshcore_transport(self):
        bridge_node = SimulatedBridgeNode(bridge_id=303)
        mesh_receiver = SimulatedBridgeNode(bridge_id=404)
        transport = FakeCompanionDatagramTransport()
        adapter = LocalFixtureBitchatAppAdapter(carrier=FakeBitchatTextCarrier())
        packet = make_android_public_message_fixture(
            sender_id=bytes.fromhex("0102030405060708"),
            timestamp_ms=0x0000018F3D2A1B00,
            text="app adapter to meshcore",
        )

        result = pump_app_adapter_bridge_once(
            mesh_node=bridge_node,
            mesh_transport=transport,
            bitchat_adapter=adapter,
            inbound_bitchat_packets=(packet.encode_raw_v1(),),
        )
        delivered = drain_transport_to_node(transport, mesh_receiver)

        self.assertEqual(
            result,
            AppAdapterBridgePumpResult(
                meshcore_notifications_delivered=0,
                meshcore_texts_published_to_app=0,
                bitchat_packets_ingested=1,
                bitchat_public_events_forwarded=1,
                meshcore_commands_sent=1,
            ),
        )
        self.assertEqual([item.text for item in delivered], ["app adapter to meshcore"])
        self.assertEqual([item.from_bridge_id for item in delivered], [303])
        self.assertEqual([item.message_id for item in delivered], [1])

    def test_combined_gate5b_pass_publishes_meshcore_text_and_forwards_fragmented_app_event(self):
        mesh_sender = SimulatedBridgeNode(bridge_id=505)
        bridge_node = SimulatedBridgeNode(bridge_id=606)
        mesh_receiver = SimulatedBridgeNode(bridge_id=707)
        transport = FakeCompanionDatagramTransport()
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
            payload=b"fragmented app event to meshcore",
        )
        raw = original.encode_raw_v1()
        frag0 = make_fragment_packet_fixture(
            original=original,
            fragment_id=b"GATE5B!!",
            index=0,
            total=2,
            fragment_data=raw[:21],
        )
        frag1 = make_fragment_packet_fixture(
            original=original,
            fragment_id=b"GATE5B!!",
            index=1,
            total=2,
            fragment_data=raw[21:],
        )

        send_text_over_transport(mesh_sender, transport, "meshcore and app same pass")
        result = pump_app_adapter_bridge_once(
            mesh_node=bridge_node,
            mesh_transport=transport,
            bitchat_adapter=adapter,
            inbound_bitchat_packets=(frag1.encode_raw_v1(), frag0.encode_raw_v1()),
        )
        delivered = drain_transport_to_node(transport, mesh_receiver)

        self.assertEqual(result.meshcore_notifications_delivered, 1)
        self.assertEqual(result.meshcore_texts_published_to_app, 1)
        self.assertEqual(result.bitchat_packets_ingested, 2)
        self.assertEqual(result.bitchat_public_events_forwarded, 1)
        self.assertEqual(result.meshcore_commands_sent, 1)
        self.assertEqual(carrier.published_texts[0].text, "meshcore and app same pass")
        self.assertEqual([item.text for item in delivered], ["fragmented app event to meshcore"])
        self.assertEqual([item.from_bridge_id for item in delivered], [606])

    def test_duplicate_app_packet_does_not_forward_twice(self):
        bridge_node = SimulatedBridgeNode(bridge_id=808)
        mesh_receiver = SimulatedBridgeNode(bridge_id=909)
        transport = FakeCompanionDatagramTransport()
        adapter = LocalFixtureBitchatAppAdapter(carrier=FakeBitchatTextCarrier())
        packet = make_android_public_message_fixture(
            sender_id=bytes.fromhex("0102030405060708"),
            timestamp_ms=0x0000018F3D2A1B00,
            text="dedupe through pump",
        ).encode_raw_v1()

        result = pump_app_adapter_bridge_once(
            mesh_node=bridge_node,
            mesh_transport=transport,
            bitchat_adapter=adapter,
            inbound_bitchat_packets=(packet, packet),
        )
        delivered = drain_transport_to_node(transport, mesh_receiver)

        self.assertEqual(result.bitchat_packets_ingested, 2)
        self.assertEqual(result.bitchat_public_events_forwarded, 1)
        self.assertEqual([item.text for item in delivered], ["dedupe through pump"])


if __name__ == "__main__":
    unittest.main()
