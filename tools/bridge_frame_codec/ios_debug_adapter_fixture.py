"""Fixture-only iOS debug bridge adapter wiring model.

This mirrors the Gate 5E Swift debug configuration and hook behavior in Python
so the bridge repo can execute the safety rules even when Xcode is unavailable.
It is not an iOS runtime, BLE stack, or stock bitchat compatibility layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .bitchat_app_adapter import BitchatAppPublicTextEvent
from .bitchat_text import BitchatTextCarrier


class IOSMeshBridgeLocalEchoMode(StrEnum):
    NONE = "none"
    APP_DEFAULT = "appDefault"
    BRIDGE_ORIGIN_SYSTEM_MESSAGE = "bridgeOriginSystemMessage"


class IOSMeshBridgePublishErrorCode(StrEnum):
    ADAPTER_DISABLED = "adapter_disabled"
    APP_NOT_READY = "app_not_ready"
    MESSAGE_TOO_LONG = "message_too_long"
    SEND_REJECTED = "send_rejected"
    PERMISSION_UNAVAILABLE = "permission_unavailable"
    TRANSPORT_UNAVAILABLE = "transport_unavailable"
    UNSUPPORTED_CHANNEL = "unsupported_channel"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True, slots=True)
class IOSMeshBridgeDebugAdapterConfiguration:
    """Disabled-by-default owner for iOS debug bridge behavior.

    The shape mirrors ``MeshBridgeDebugAdapterConfiguration`` in the local iOS
    checkout: inbound and outbound behavior are independently gated, and the
    default enables nothing.
    """

    inbound_events_enabled: bool = False
    outbound_publish_enabled: bool = False
    local_echo_mode: IOSMeshBridgeLocalEchoMode = IOSMeshBridgeLocalEchoMode.NONE

    @property
    def enables_any_bridge_behavior(self) -> bool:
        return self.inbound_events_enabled or self.outbound_publish_enabled


IOS_MESH_BRIDGE_DEBUG_DISABLED = IOSMeshBridgeDebugAdapterConfiguration()


@dataclass(frozen=True, slots=True)
class IOSMeshBridgePublishPublicTextResult:
    accepted_for_send: bool
    app_message_id: str | None = None
    packet_id_hex: str | None = None
    error_code: IOSMeshBridgePublishErrorCode | None = None
    error_message: str | None = None

    @classmethod
    def disabled(cls) -> "IOSMeshBridgePublishPublicTextResult":
        return cls(
            accepted_for_send=False,
            error_code=IOSMeshBridgePublishErrorCode.ADAPTER_DISABLED,
            error_message="Mesh bridge app adapter is disabled",
        )


@dataclass(slots=True)
class IOSDebugMeshBridgeAdapterFixture:
    """Executable fixture for the iOS Gate 5E debug hooks.

    ``record_accepted_public_text`` models the no-op-by-default inbound hook.
    ``debug_publish_bridge_public_text`` models the ``BLEService`` debug wrapper:
    it accepts into the app send pipeline only when outbound config is explicit.
    """

    carrier: BitchatTextCarrier
    configuration: IOSMeshBridgeDebugAdapterConfiguration = IOS_MESH_BRIDGE_DEBUG_DISABLED
    emitted_events: list[BitchatAppPublicTextEvent] = field(default_factory=list)
    max_message_length: int = 60_000

    @property
    def is_enabled(self) -> bool:
        return self.configuration.enables_any_bridge_behavior

    @property
    def local_echo_mode(self) -> IOSMeshBridgeLocalEchoMode:
        return self.configuration.local_echo_mode

    def record_accepted_public_text(self, event: BitchatAppPublicTextEvent) -> list[BitchatAppPublicTextEvent]:
        if not self.configuration.inbound_events_enabled or not event.accepted:
            return []
        self.emitted_events.append(event)
        return [event]

    def debug_publish_bridge_public_text(
        self,
        text: str,
        *,
        from_bridge_id: int,
        message_id: int,
        timestamp_ms: int | None = None,
        nickname: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> IOSMeshBridgePublishPublicTextResult:
        _ = timestamp_ms, nickname, metadata
        if not self.configuration.outbound_publish_enabled:
            return IOSMeshBridgePublishPublicTextResult.disabled()
        if len(text) > self.max_message_length:
            return IOSMeshBridgePublishPublicTextResult(
                accepted_for_send=False,
                error_code=IOSMeshBridgePublishErrorCode.MESSAGE_TOO_LONG,
                error_message="Message too long for app public-send path",
            )

        app_message_id = f"meshbridge-{from_bridge_id}-{message_id}"
        self.carrier.publish_public_text(text, from_bridge_id=from_bridge_id, message_id=message_id)
        return IOSMeshBridgePublishPublicTextResult(
            accepted_for_send=True,
            app_message_id=app_message_id,
        )
