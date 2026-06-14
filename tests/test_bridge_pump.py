import unittest

from tools.bridge_frame_codec import (
    BitchatPublishedText,
    BridgePumpResult,
    FakeBitchatTextCarrier,
    FakeCompanionDatagramTransport,
    MAX_FRAME_PAYLOAD,
    SimulatedBridgeNode,
    drain_transport_to_node,
    pump_text_bridge_once,
    send_text_over_transport,
)


class BridgePumpTests(unittest.TestCase):
    def test_pump_drains_meshcore_delivered_text_into_bitchat_carrier(self):
        mesh_sender = SimulatedBridgeNode(bridge_id=111)
        bridge_node = SimulatedBridgeNode(bridge_id=222)
        transport = FakeCompanionDatagramTransport()
        carrier = FakeBitchatTextCarrier()

        commands_sent = send_text_over_transport(
            mesh_sender,
            transport,
            "meshcore delivered text",
        )
        result = pump_text_bridge_once(
            mesh_node=bridge_node,
            mesh_transport=transport,
            bitchat_carrier=carrier,
        )

        self.assertEqual(commands_sent, 1)
        self.assertEqual(
            result,
            BridgePumpResult(
                meshcore_notifications_delivered=1,
                meshcore_texts_published=1,
                bitchat_texts_forwarded=0,
                meshcore_commands_sent=0,
            ),
        )
        self.assertEqual(
            carrier.published_texts,
            [
                BitchatPublishedText(
                    text="meshcore delivered text",
                    from_bridge_id=111,
                    message_id=1,
                )
            ],
        )
        self.assertEqual(bridge_node.inbox, [])
        self.assertIsNone(transport.recv_channel_data_notification())

    def test_pump_forwards_bitchat_originated_text_over_meshcore_transport(self):
        bridge_node = SimulatedBridgeNode(bridge_id=333)
        mesh_receiver = SimulatedBridgeNode(bridge_id=444)
        transport = FakeCompanionDatagramTransport()
        carrier = FakeBitchatTextCarrier()
        carrier.queue_public_text("carrier public text", carrier_message_id="fake-1")

        result = pump_text_bridge_once(
            mesh_node=bridge_node,
            mesh_transport=transport,
            bitchat_carrier=carrier,
        )
        delivered = drain_transport_to_node(transport, mesh_receiver)

        self.assertEqual(
            result,
            BridgePumpResult(
                meshcore_notifications_delivered=0,
                meshcore_texts_published=0,
                bitchat_texts_forwarded=1,
                meshcore_commands_sent=1,
            ),
        )
        self.assertEqual(carrier.published_texts, [])
        self.assertEqual([item.text for item in delivered], ["carrier public text"])
        self.assertEqual([item.from_bridge_id for item in delivered], [333])
        self.assertEqual([item.message_id for item in delivered], [1])
        self.assertIsNone(carrier.recv_public_text())

    def test_pump_combines_both_directions_and_counts_fragmented_sends(self):
        mesh_sender = SimulatedBridgeNode(bridge_id=555)
        bridge_node = SimulatedBridgeNode(bridge_id=666)
        mesh_receiver = SimulatedBridgeNode(bridge_id=777)
        transport = FakeCompanionDatagramTransport()
        carrier = FakeBitchatTextCarrier()
        long_carrier_text = "bitchat to meshcore " + ("x" * (MAX_FRAME_PAYLOAD + 3))

        send_text_over_transport(mesh_sender, transport, "meshcore to bitchat")
        carrier.queue_public_text(long_carrier_text, carrier_message_id="fake-long")

        result = pump_text_bridge_once(
            mesh_node=bridge_node,
            mesh_transport=transport,
            bitchat_carrier=carrier,
        )
        delivered = drain_transport_to_node(transport, mesh_receiver)

        self.assertEqual(result.meshcore_notifications_delivered, 1)
        self.assertEqual(result.meshcore_texts_published, 1)
        self.assertEqual(result.bitchat_texts_forwarded, 1)
        self.assertGreater(result.meshcore_commands_sent, 1)
        self.assertEqual(
            carrier.published_texts,
            [
                BitchatPublishedText(
                    text="meshcore to bitchat",
                    from_bridge_id=555,
                    message_id=1,
                )
            ],
        )
        self.assertEqual([item.text for item in delivered], [long_carrier_text])
        self.assertEqual([item.from_bridge_id for item in delivered], [666])


if __name__ == "__main__":
    unittest.main()
