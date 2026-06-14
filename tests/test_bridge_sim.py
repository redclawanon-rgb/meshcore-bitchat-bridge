import unittest

from tools.bridge_frame_codec import BridgeFrameError, MAX_FRAME_PAYLOAD
from tools.bridge_frame_codec.sim import SimulatedBridgeNode, SimulatedMeshCoreLink


class BridgeSimulatorTests(unittest.TestCase):
    def test_one_frame_text_a_to_b(self):
        alice = SimulatedBridgeNode(bridge_id=0xA1)
        bob = SimulatedBridgeNode(bridge_id=0xB2)
        link = SimulatedMeshCoreLink()

        delivered = link.deliver(alice, bob, "hello over MeshCore")

        self.assertEqual(len(delivered), 1)
        self.assertEqual(delivered[0].from_bridge_id, 0xA1)
        self.assertEqual(delivered[0].message_id, 1)
        self.assertEqual(delivered[0].text, "hello over MeshCore")
        self.assertEqual(bob.inbox, delivered)

    def test_bidirectional_text_exchange(self):
        alice = SimulatedBridgeNode(bridge_id=1)
        bob = SimulatedBridgeNode(bridge_id=2)
        link = SimulatedMeshCoreLink()

        self.assertEqual(link.deliver(alice, bob, "A to B")[0].text, "A to B")
        self.assertEqual(link.deliver(bob, alice, "B to A")[0].text, "B to A")

        self.assertEqual([item.text for item in alice.inbox], ["B to A"])
        self.assertEqual([item.text for item in bob.inbox], ["A to B"])

    def test_multi_frame_text_roundtrip(self):
        alice = SimulatedBridgeNode(bridge_id=1)
        bob = SimulatedBridgeNode(bridge_id=2)
        link = SimulatedMeshCoreLink()
        text = "x" * (MAX_FRAME_PAYLOAD * 2 + 17)

        delivered = link.deliver(alice, bob, text)

        self.assertEqual(len(delivered), 1)
        self.assertEqual(delivered[0].text, text)
        self.assertEqual(len(bob.inbox), 1)

    def test_duplicate_notification_is_ignored_after_delivery(self):
        alice = SimulatedBridgeNode(bridge_id=1)
        bob = SimulatedBridgeNode(bridge_id=2)
        link = SimulatedMeshCoreLink()
        command = alice.make_text_commands("duplicate-safe")[0]
        notification = link.command_to_notification(command)

        first = bob.receive_notification(notification)
        second = bob.receive_notification(notification)

        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual([item.text for item in bob.inbox], ["duplicate-safe"])

    def test_duplicate_partial_fragment_is_ignored(self):
        alice = SimulatedBridgeNode(bridge_id=1)
        bob = SimulatedBridgeNode(bridge_id=2)
        link = SimulatedMeshCoreLink()
        text = "z" * (MAX_FRAME_PAYLOAD + 1)
        commands = alice.make_text_commands(text)
        first_fragment = link.command_to_notification(commands[0])
        second_fragment = link.command_to_notification(commands[1])

        self.assertIsNone(bob.receive_notification(first_fragment))
        self.assertIsNone(bob.receive_notification(first_fragment))
        delivered = bob.receive_notification(second_fragment)

        self.assertIsNotNone(delivered)
        assert delivered is not None
        self.assertEqual(delivered.text, text)
        self.assertEqual(len(bob.inbox), 1)

    def test_corrupt_bridge_frame_is_rejected(self):
        alice = SimulatedBridgeNode(bridge_id=1)
        bob = SimulatedBridgeNode(bridge_id=2)
        link = SimulatedMeshCoreLink()
        command = bytearray(alice.make_text_commands("corrupt me")[0])
        command[-1] ^= 0xFF
        notification = link.command_to_notification(bytes(command))

        with self.assertRaisesRegex(BridgeFrameError, "crc mismatch"):
            bob.receive_notification(notification)
        self.assertEqual(bob.inbox, [])


if __name__ == "__main__":
    unittest.main()
