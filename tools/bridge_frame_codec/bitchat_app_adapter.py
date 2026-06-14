"""App-native bitchat adapter seam for local Gate 5A tests.

This module defines the boundary a future Android/iOS/native integration should
satisfy without pretending this Python process is a stock BLE bitchat peer.
The included local implementation is fixture-only: it consumes deterministic
packet bytes from the Gate 4 conformance helpers and emits semantic public-text
events for the bridge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .bitchat_packet_fixture import (
    BITCHAT_MESSAGE_TYPE_FRAGMENT,
    BITCHAT_MESSAGE_TYPE_MESSAGE,
    BitchatFragmentPayloadFixture,
    BitchatPacketFixture,
    BitchatPacketFixtureError,
    compute_packet_id_hex_fixture,
    decode_fragment_payload_fixture,
    decode_wire_v1_packet_fixture,
    reassemble_fragment_payload_fixtures,
)
from .bitchat_text import BitchatTextCarrier


class BitchatAppAdapterError(ValueError):
    """Raised when fixture bytes cannot be adapted into the local app seam."""


@dataclass(frozen=True, slots=True)
class BitchatAppPublicTextEvent:
    """Semantic public text emitted by a future app-native bitchat integration.

    The event is intentionally semantic. It carries enough metadata for bridge
    deduplication/diagnostics while keeping app-specific BLE/session lifecycle
    details outside the MeshCore bridge core.
    """

    text: str
    packet_id_hex: str
    sender_id: bytes
    timestamp_ms: int
    route: tuple[bytes, ...] | None = None
    nickname: str | None = None
    app_message_id: str | None = None
    platform: str = "fixture"
    accepted: bool = True
    source: str = "fixture"


class BitchatAppAdapter(Protocol):
    """Boundary expected from a future app-native bitchat adapter.

    A real implementation may sit inside Android/iOS or beside a companion
    service. It should translate app-native packet/message callbacks into
    semantic public-text events and accept bridge-delivered text through an app
    API. It should not require the MeshCore bridge core to know BLE, Noise,
    mobile lifecycle, or trust UI details.
    """

    def ingest_packet_bytes(self, data: bytes) -> list[BitchatAppPublicTextEvent]:
        """Ingest one app/native packet byte blob and return semantic events."""
        raise NotImplementedError

    def publish_bridge_text(self, text: str, *, from_bridge_id: int, message_id: int) -> None:
        """Publish bridge-delivered public text into the app/native side."""
        raise NotImplementedError


@dataclass(slots=True)
class LocalFixtureBitchatAppAdapter:
    """Fixture-only implementation of the app-native adapter boundary.

    It accepts bytes decodable by ``decode_wire_v1_packet_fixture``. Public
    message packets produce one semantic event unless their packet ID was seen
    before. Fragment packets are buffered by fragment ID until complete, then
    reassembled and recursively adapted as the original packet bytes.

    This does not implement BLE stream assembly, route planning, Noise,
    app lifecycle, persistence, trust UI, or stock interoperability.
    """

    carrier: BitchatTextCarrier
    seen_packet_ids: set[str] = field(default_factory=set)
    fragment_buffers: dict[bytes, dict[int, BitchatFragmentPayloadFixture]] = field(default_factory=dict)

    def ingest_packet_bytes(self, data: bytes) -> list[BitchatAppPublicTextEvent]:
        try:
            packet = decode_wire_v1_packet_fixture(data)
        except BitchatPacketFixtureError as exc:
            raise BitchatAppAdapterError("could not decode bitchat fixture packet") from exc
        return self.ingest_packet(packet)

    def ingest_packet(self, packet: BitchatPacketFixture) -> list[BitchatAppPublicTextEvent]:
        """Ingest an already-decoded fixture packet."""

        packet_id_hex = compute_packet_id_hex_fixture(packet)
        if packet_id_hex in self.seen_packet_ids:
            return []

        if packet.packet_type == BITCHAT_MESSAGE_TYPE_FRAGMENT:
            # Mark the fragment packet itself as seen to avoid processing exact
            # duplicates, but only mark the reassembled original when it emits.
            self.seen_packet_ids.add(packet_id_hex)
            return self._ingest_fragment_packet(packet)

        if packet.packet_type != BITCHAT_MESSAGE_TYPE_MESSAGE:
            self.seen_packet_ids.add(packet_id_hex)
            return []

        try:
            text = packet.public_text
        except BitchatPacketFixtureError as exc:
            raise BitchatAppAdapterError("public message payload is not UTF-8 text") from exc

        self.seen_packet_ids.add(packet_id_hex)
        return [
            BitchatAppPublicTextEvent(
                text=text,
                packet_id_hex=packet_id_hex,
                sender_id=packet.sender_id,
                timestamp_ms=packet.timestamp_ms,
                route=packet.route,
            )
        ]

    def publish_bridge_text(self, text: str, *, from_bridge_id: int, message_id: int) -> None:
        self.carrier.publish_public_text(
            text,
            from_bridge_id=from_bridge_id,
            message_id=message_id,
        )

    def _ingest_fragment_packet(self, packet: BitchatPacketFixture) -> list[BitchatAppPublicTextEvent]:
        try:
            fragment = decode_fragment_payload_fixture(packet.payload)
        except BitchatPacketFixtureError as exc:
            raise BitchatAppAdapterError("could not decode fragment payload") from exc

        buffer = self.fragment_buffers.setdefault(fragment.fragment_id, {})
        existing = buffer.get(fragment.index)
        if existing is not None:
            if existing.data == fragment.data:
                return []
            raise BitchatAppAdapterError("conflicting duplicate fragment")
        buffer[fragment.index] = fragment

        if len(buffer) < fragment.total:
            return []

        try:
            reassembled = reassemble_fragment_payload_fixtures(list(buffer.values()))
        except BitchatPacketFixtureError as exc:
            raise BitchatAppAdapterError("could not reassemble fragment payloads") from exc
        finally:
            self.fragment_buffers.pop(fragment.fragment_id, None)

        return self.ingest_packet_bytes(reassembled)
