"""Version-pinned bitchat packet fixture helpers for adapter research.

This module intentionally implements only a small, deterministic subset of the
upstream bitchat packet shape observed during Gate 4 research. It is for local
fixture/conformance tests only. It does not implement BLE, padding,
compression, fragmentation, signing, signature verification, Noise, peer
verification, or stock bitchat interoperability.
"""

from __future__ import annotations

from dataclasses import dataclass

BITCHAT_PACKET_VERSION_V1 = 1
BITCHAT_MESSAGE_TYPE_MESSAGE = 0x02
BITCHAT_RECIPIENT_BROADCAST = b"\xff" * 8
BITCHAT_SENDER_ID_SIZE = 8
BITCHAT_RECIPIENT_ID_SIZE = 8
BITCHAT_SIGNATURE_SIZE = 64
BITCHAT_HEADER_SIZE_V1 = 14

_FLAG_HAS_RECIPIENT = 0x01
_FLAG_HAS_SIGNATURE = 0x02
_FLAG_IS_COMPRESSED = 0x04
_FLAG_HAS_ROUTE = 0x08


class BitchatPacketFixtureError(ValueError):
    """Raised when a local research fixture packet is malformed."""


@dataclass(frozen=True, slots=True)
class BitchatPacketFixture:
    """Small raw v1 `BitchatPacket` fixture representation.

    Field layout mirrors the upstream v1 raw/unpadded binary shape:

    - version: 1 byte
    - type: 1 byte
    - ttl: 1 byte
    - timestamp: 8 bytes big-endian milliseconds
    - flags: 1 byte
    - payload length: 2 bytes big-endian
    - sender ID: 8 bytes
    - optional recipient ID: 8 bytes
    - payload bytes
    - optional signature: 64 bytes

    Upstream encoders may add padding and may compress payloads; this fixture
    helper does neither. Upstream decoders observed in Android try raw decode
    first and then unpad, which makes raw fixtures useful for deterministic
    field tests without claiming app interoperability.
    """

    version: int
    packet_type: int
    ttl: int
    timestamp_ms: int
    sender_id: bytes
    payload: bytes
    recipient_id: bytes | None = None
    signature: bytes | None = None

    def encode_raw_v1(self) -> bytes:
        """Encode this fixture as raw unpadded bitchat v1 packet bytes."""

        if self.version != BITCHAT_PACKET_VERSION_V1:
            raise BitchatPacketFixtureError("only v1 fixture packets are supported")
        _validate_byte("packet_type", self.packet_type)
        _validate_byte("ttl", self.ttl)
        if self.timestamp_ms < 0 or self.timestamp_ms > 0xFFFF_FFFF_FFFF_FFFF:
            raise BitchatPacketFixtureError("timestamp_ms must fit uint64")
        if len(self.sender_id) != BITCHAT_SENDER_ID_SIZE:
            raise BitchatPacketFixtureError("sender_id must be exactly 8 bytes")
        if len(self.payload) > 0xFFFF:
            raise BitchatPacketFixtureError("v1 payload must fit uint16 length")
        flags = 0
        if self.recipient_id is not None:
            if len(self.recipient_id) != BITCHAT_RECIPIENT_ID_SIZE:
                raise BitchatPacketFixtureError("recipient_id must be exactly 8 bytes")
            flags |= _FLAG_HAS_RECIPIENT
        if self.signature is not None:
            if len(self.signature) != BITCHAT_SIGNATURE_SIZE:
                raise BitchatPacketFixtureError("signature must be exactly 64 bytes")
            flags |= _FLAG_HAS_SIGNATURE

        parts = [
            bytes([self.version, self.packet_type, self.ttl]),
            self.timestamp_ms.to_bytes(8, "big"),
            bytes([flags]),
            len(self.payload).to_bytes(2, "big"),
            self.sender_id,
        ]
        if self.recipient_id is not None:
            parts.append(self.recipient_id)
        parts.append(self.payload)
        if self.signature is not None:
            parts.append(self.signature)
        return b"".join(parts)

    @property
    def public_text(self) -> str:
        """Decode payload as UTF-8 public text for fixture assertions."""

        try:
            return self.payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BitchatPacketFixtureError("payload is not UTF-8 public text") from exc

    @property
    def has_broadcast_recipient(self) -> bool:
        """Whether this fixture uses the Android-observed broadcast recipient."""

        return self.recipient_id == BITCHAT_RECIPIENT_BROADCAST


def decode_raw_v1_packet_fixture(data: bytes) -> BitchatPacketFixture:
    """Decode raw unpadded bitchat v1 packet fixture bytes.

    Rejects compressed and route-flagged packets because Gate 4A fixtures are
    limited to raw public text packet field conformance.
    """

    if len(data) < BITCHAT_HEADER_SIZE_V1 + BITCHAT_SENDER_ID_SIZE:
        raise BitchatPacketFixtureError("packet too short for v1 header and sender")
    version = data[0]
    if version != BITCHAT_PACKET_VERSION_V1:
        raise BitchatPacketFixtureError("only v1 fixture packets are supported")
    packet_type = data[1]
    ttl = data[2]
    timestamp_ms = int.from_bytes(data[3:11], "big")
    flags = data[11]
    if flags & _FLAG_IS_COMPRESSED:
        raise BitchatPacketFixtureError("compressed packets are outside fixture scope")
    if flags & _FLAG_HAS_ROUTE:
        raise BitchatPacketFixtureError("route packets are outside v1 fixture scope")
    payload_len = int.from_bytes(data[12:14], "big")
    offset = BITCHAT_HEADER_SIZE_V1
    sender_id = data[offset : offset + BITCHAT_SENDER_ID_SIZE]
    offset += BITCHAT_SENDER_ID_SIZE
    recipient_id = None
    if flags & _FLAG_HAS_RECIPIENT:
        if len(data) < offset + BITCHAT_RECIPIENT_ID_SIZE:
            raise BitchatPacketFixtureError("packet too short for recipient")
        recipient_id = data[offset : offset + BITCHAT_RECIPIENT_ID_SIZE]
        offset += BITCHAT_RECIPIENT_ID_SIZE
    if len(data) < offset + payload_len:
        raise BitchatPacketFixtureError("packet too short for payload")
    payload = data[offset : offset + payload_len]
    offset += payload_len
    signature = None
    if flags & _FLAG_HAS_SIGNATURE:
        if len(data) < offset + BITCHAT_SIGNATURE_SIZE:
            raise BitchatPacketFixtureError("packet too short for signature")
        signature = data[offset : offset + BITCHAT_SIGNATURE_SIZE]
        offset += BITCHAT_SIGNATURE_SIZE
    if offset != len(data):
        raise BitchatPacketFixtureError("trailing bytes after fixture packet")
    return BitchatPacketFixture(
        version=version,
        packet_type=packet_type,
        ttl=ttl,
        timestamp_ms=timestamp_ms,
        sender_id=sender_id,
        recipient_id=recipient_id,
        payload=payload,
        signature=signature,
    )


def make_ios_public_message_fixture(*, sender_id: bytes, timestamp_ms: int, text: str, ttl: int = 7) -> BitchatPacketFixture:
    """Create the iOS-observed public-message shape: no recipient ID."""

    return BitchatPacketFixture(
        version=BITCHAT_PACKET_VERSION_V1,
        packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
        ttl=ttl,
        timestamp_ms=timestamp_ms,
        sender_id=sender_id,
        recipient_id=None,
        payload=text.encode("utf-8"),
        signature=None,
    )


def make_android_public_message_fixture(*, sender_id: bytes, timestamp_ms: int, text: str, ttl: int = 7) -> BitchatPacketFixture:
    """Create the Android-observed public-message shape: broadcast recipient ID."""

    return BitchatPacketFixture(
        version=BITCHAT_PACKET_VERSION_V1,
        packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
        ttl=ttl,
        timestamp_ms=timestamp_ms,
        sender_id=sender_id,
        recipient_id=BITCHAT_RECIPIENT_BROADCAST,
        payload=text.encode("utf-8"),
        signature=None,
    )


def _validate_byte(name: str, value: int) -> None:
    if value < 0 or value > 0xFF:
        raise BitchatPacketFixtureError(f"{name} must fit uint8")
