import unittest

from tools.bridge_frame_codec import (
    BitchatAppPublicTextEvent,
    FakeBitchatTextCarrier,
    IOSDebugMeshBridgeAdapterFixture,
    IOSMeshBridgeDebugAdapterConfiguration,
    IOSMeshBridgeLocalEchoMode,
    IOSMeshBridgePublishErrorCode,
    IOS_MESH_BRIDGE_DEBUG_DISABLED,
)


class IOSDebugAdapterConfigFixtureTests(unittest.TestCase):
    def make_event(self, text="accepted app text", *, accepted=True):
        return BitchatAppPublicTextEvent(
            text=text,
            packet_id_hex="packet-id-123",
            sender_id=bytes.fromhex("0102030405060708"),
            timestamp_ms=1_700_000_000_000,
            nickname="Alice",
            app_message_id="app-msg-1",
            platform="ios",
            accepted=accepted,
            source="ios-app",
        )

    def test_disabled_configuration_is_fully_noop(self):
        carrier = FakeBitchatTextCarrier()
        adapter = IOSDebugMeshBridgeAdapterFixture(carrier=carrier)

        inbound = adapter.record_accepted_public_text(self.make_event())
        outbound = adapter.debug_publish_bridge_public_text(
            "meshcore delivered",
            from_bridge_id=7,
            message_id=42,
        )

        self.assertEqual(adapter.configuration, IOS_MESH_BRIDGE_DEBUG_DISABLED)
        self.assertFalse(adapter.is_enabled)
        self.assertEqual(adapter.local_echo_mode, IOSMeshBridgeLocalEchoMode.NONE)
        self.assertEqual(inbound, [])
        self.assertEqual(adapter.emitted_events, [])
        self.assertEqual(carrier.published_texts, [])
        self.assertFalse(outbound.accepted_for_send)
        self.assertEqual(outbound.error_code, IOSMeshBridgePublishErrorCode.ADAPTER_DISABLED)

    def test_inbound_only_emits_accepted_events_but_refuses_outbound(self):
        carrier = FakeBitchatTextCarrier()
        adapter = IOSDebugMeshBridgeAdapterFixture(
            carrier=carrier,
            configuration=IOSMeshBridgeDebugAdapterConfiguration(inbound_events_enabled=True),
        )

        accepted = adapter.record_accepted_public_text(self.make_event("accepted"))
        rejected = adapter.record_accepted_public_text(self.make_event("rejected", accepted=False))
        outbound = adapter.debug_publish_bridge_public_text("blocked", from_bridge_id=1, message_id=2)

        self.assertTrue(adapter.is_enabled)
        self.assertEqual([event.text for event in accepted], ["accepted"])
        self.assertEqual(rejected, [])
        self.assertEqual([event.text for event in adapter.emitted_events], ["accepted"])
        self.assertEqual(carrier.published_texts, [])
        self.assertEqual(outbound.error_code, IOSMeshBridgePublishErrorCode.ADAPTER_DISABLED)

    def test_outbound_only_publishes_through_app_send_fixture_but_emits_no_inbound(self):
        carrier = FakeBitchatTextCarrier()
        adapter = IOSDebugMeshBridgeAdapterFixture(
            carrier=carrier,
            configuration=IOSMeshBridgeDebugAdapterConfiguration(outbound_publish_enabled=True),
        )

        inbound = adapter.record_accepted_public_text(self.make_event("ignored inbound"))
        outbound = adapter.debug_publish_bridge_public_text(
            "meshcore delivered",
            from_bridge_id=9,
            message_id=1001,
            timestamp_ms=1_700_000_000_000,
            nickname="Bridge",
            metadata={"source": "meshcore"},
        )

        self.assertEqual(inbound, [])
        self.assertEqual(adapter.emitted_events, [])
        self.assertTrue(outbound.accepted_for_send)
        self.assertEqual(outbound.app_message_id, "meshbridge-9-1001")
        self.assertEqual(outbound.error_code, None)
        self.assertEqual(len(carrier.published_texts), 1)
        self.assertEqual(carrier.published_texts[0].text, "meshcore delivered")
        self.assertEqual(carrier.published_texts[0].from_bridge_id, 9)
        self.assertEqual(carrier.published_texts[0].message_id, 1001)

    def test_fully_enabled_preserves_local_echo_mode_and_both_directions(self):
        carrier = FakeBitchatTextCarrier()
        adapter = IOSDebugMeshBridgeAdapterFixture(
            carrier=carrier,
            configuration=IOSMeshBridgeDebugAdapterConfiguration(
                inbound_events_enabled=True,
                outbound_publish_enabled=True,
                local_echo_mode=IOSMeshBridgeLocalEchoMode.APP_DEFAULT,
            ),
        )

        adapter.record_accepted_public_text(self.make_event("app to bridge"))
        outbound = adapter.debug_publish_bridge_public_text("bridge to app", from_bridge_id=3, message_id=4)

        self.assertTrue(adapter.is_enabled)
        self.assertEqual(adapter.local_echo_mode, IOSMeshBridgeLocalEchoMode.APP_DEFAULT)
        self.assertEqual([event.text for event in adapter.emitted_events], ["app to bridge"])
        self.assertEqual([item.text for item in carrier.published_texts], ["bridge to app"])
        self.assertTrue(outbound.accepted_for_send)
        self.assertEqual(outbound.app_message_id, "meshbridge-3-4")

    def test_outbound_length_rejection_does_not_publish(self):
        carrier = FakeBitchatTextCarrier()
        adapter = IOSDebugMeshBridgeAdapterFixture(
            carrier=carrier,
            configuration=IOSMeshBridgeDebugAdapterConfiguration(outbound_publish_enabled=True),
            max_message_length=5,
        )

        result = adapter.debug_publish_bridge_public_text("too long", from_bridge_id=1, message_id=2)

        self.assertFalse(result.accepted_for_send)
        self.assertEqual(result.error_code, IOSMeshBridgePublishErrorCode.MESSAGE_TOO_LONG)
        self.assertEqual(carrier.published_texts, [])


if __name__ == "__main__":
    unittest.main()
