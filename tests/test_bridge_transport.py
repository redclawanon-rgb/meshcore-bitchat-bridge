import unittest

from tools.bridge_frame_codec import MAX_FRAME_PAYLOAD
from tools.bridge_frame_codec.meshcore_companion import CMD_SEND_CHANNEL_DATA
from tools.bridge_frame_codec.sim import SimulatedBridgeNode
from tools.bridge_frame_codec.transport import (
    FakeCompanionDatagramTransport,
    drain_transport_to_node,
    send_text_over_transport,
)


class BridgeTransportTests(unittest.TestCase):
    def test_fake_transport_carries_one_frame_message(self):
        alice = SimulatedBridgeNode(bridge_id=1)
        bob = SimulatedBridgeNode(bridge_id=2)
        transport = FakeCompanionDatagramTransport()

        count = send_text_over_transport(alice, transport, "transport hello")
        delivered = drain_transport_to_node(transport, bob)

        self.assertEqual(count, 1)
        self.assertEqual(len(transport.sent_commands), 1)
        self.assertEqual(transport.sent_commands[0][0], CMD_SEND_CHANNEL_DATA)
        self.assertEqual([item.text for item in delivered], ["transport hello"])
        self.assertEqual([item.text for item in bob.inbox], ["transport hello"])
        self.assertIsNone(transport.recv_channel_data_notification())

    def test_fake_transport_carries_multi_frame_message(self):
        alice = SimulatedBridgeNode(bridge_id=1)
        bob = SimulatedBridgeNode(bridge_id=2)
        transport = FakeCompanionDatagramTransport()
        text = "y" * (MAX_FRAME_PAYLOAD * 3 + 5)

        count = send_text_over_transport(alice, transport, text)
        delivered = drain_transport_to_node(transport, bob)

        self.assertGreater(count, 1)
        self.assertEqual(len(transport.sent_commands), count)
        self.assertEqual(len(delivered), 1)
        self.assertEqual(delivered[0].text, text)

    def test_drain_is_safe_when_no_notifications_are_queued(self):
        bob = SimulatedBridgeNode(bridge_id=2)
        transport = FakeCompanionDatagramTransport()

        self.assertEqual(drain_transport_to_node(transport, bob), [])
        self.assertEqual(bob.inbox, [])


if __name__ == "__main__":
    unittest.main()
