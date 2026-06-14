import unittest

from tools.bridge_frame_codec import (
    BitchatOutboundText,
    BitchatPublishedText,
    FakeBitchatTextCarrier,
)
from tools.bridge_frame_codec.bitchat_text import BitchatTextCarrier
from tools.bridge_frame_codec.sim import SimulatedBridgeNode, SimulatedMeshCoreLink
from tools.bridge_frame_codec.transport import (
    FakeCompanionDatagramTransport,
    drain_transport_to_node,
    send_text_over_transport,
)


class BitchatTextCarrierTests(unittest.TestCase):
    def test_decoded_delivered_text_can_be_published_to_fake_carrier(self):
        alice = SimulatedBridgeNode(bridge_id=101)
        bridge_receiver = SimulatedBridgeNode(bridge_id=202)
        link = SimulatedMeshCoreLink()
        carrier = FakeBitchatTextCarrier()

        delivered = link.deliver(alice, bridge_receiver, "decoded text for carrier")
        self.assertEqual(len(delivered), 1)
        item = delivered[0]

        carrier.publish_public_text(
            item.text,
            from_bridge_id=item.from_bridge_id,
            message_id=item.message_id,
        )

        self.assertEqual(
            carrier.published_texts,
            [
                BitchatPublishedText(
                    text="decoded text for carrier",
                    from_bridge_id=101,
                    message_id=1,
                )
            ],
        )
        self.assertEqual(bridge_receiver.inbox, delivered)

    def test_fake_carrier_originated_text_uses_meshcore_transport_neutral_path(self):
        carrier = FakeBitchatTextCarrier()
        mesh_sender = SimulatedBridgeNode(bridge_id=303)
        mesh_receiver = SimulatedBridgeNode(bridge_id=404)
        transport = FakeCompanionDatagramTransport()
        carrier.queue_public_text(
            "carrier originated public text",
            carrier_message_id="fake-carrier-1",
        )

        outbound = carrier.recv_public_text()
        self.assertEqual(
            outbound,
            BitchatOutboundText(
                text="carrier originated public text",
                carrier_message_id="fake-carrier-1",
            ),
        )
        assert outbound is not None
        count = send_text_over_transport(mesh_sender, transport, outbound.text)
        delivered = drain_transport_to_node(transport, mesh_receiver)

        self.assertEqual(count, 1)
        self.assertEqual([item.text for item in delivered], [outbound.text])
        self.assertEqual([item.from_bridge_id for item in delivered], [303])
        self.assertEqual([item.message_id for item in delivered], [1])
        self.assertEqual([item.text for item in mesh_receiver.inbox], [outbound.text])
        self.assertIsNone(carrier.recv_public_text())

    def test_fake_carrier_matches_protocol_and_keeps_text_only_boundary(self):
        carrier: BitchatTextCarrier = FakeBitchatTextCarrier()

        carrier.publish_public_text("hello", from_bridge_id=1, message_id=2)
        self.assertIsNone(carrier.recv_public_text())

        fake = carrier
        self.assertEqual(fake.published_texts[0].text, "hello")
        self.assertFalse(hasattr(fake.published_texts[0], "payload"))
        self.assertFalse(hasattr(BitchatOutboundText(text="x"), "packet"))


if __name__ == "__main__":
    unittest.main()
