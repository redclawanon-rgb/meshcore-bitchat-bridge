"""Version-pinned bitchat packet fixture helpers for adapter research.

This module intentionally implements only a small, deterministic subset of the
upstream bitchat packet shape observed during Gate 4 research. It is for local
fixture/conformance tests only. It does not implement BLE, fragmentation,
signing, signature verification, Noise, peer verification, or stock bitchat
interoperability.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import zlib

BITCHAT_PACKET_VERSION_V1 = 1
BITCHAT_PACKET_VERSION_V2 = 2
BITCHAT_MESSAGE_TYPE_MESSAGE = 0x02
BITCHAT_MESSAGE_TYPE_FRAGMENT = 0x20
BITCHAT_RECIPIENT_BROADCAST = b"\xff" * 8
BITCHAT_SENDER_ID_SIZE = 8
BITCHAT_RECIPIENT_ID_SIZE = 8
BITCHAT_SIGNATURE_SIZE = 64
BITCHAT_ROUTE_HOP_SIZE = 8
BITCHAT_HEADER_SIZE_V1 = 14
BITCHAT_HEADER_SIZE_V2 = 16
BITCHAT_SYNC_TTL_HOPS = 0
BITCHAT_FRAGMENT_HEADER_SIZE = 13
BITCHAT_FRAGMENT_ID_SIZE = 8
BITCHAT_COMPRESSION_THRESHOLD_BYTES = 100
BITCHAT_PADDING_BLOCK_SIZES = (256, 512, 1024, 2048)
BITCHAT_COMPRESSION_BOMB_RATIO_LIMIT = 50_000.0

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
    route: tuple[bytes, ...] | None = None

    def encode_raw_v1(self) -> bytes:
        """Encode this fixture as raw unpadded, uncompressed bitchat bytes."""

        return self._encode_unpadded_v1(allow_compression=False)

    def encode_wire_v1(self, *, apply_padding: bool = True, allow_compression: bool = True) -> bytes:
        """Encode this fixture with the upstream-observed v1 wire transformations.

        This applies raw-deflate compression only when the payload passes the
        Android-observed threshold/entropy/benefit checks. Padding uses the
        observed PKCS#7-style block normalization. The result is still a local
        fixture, not a stock compatibility claim.
        """

        raw = self._encode_unpadded_v1(allow_compression=allow_compression)
        if apply_padding:
            return pad_fixture_packet(raw, optimal_padding_block_size(len(raw)))
        return raw

    def encode_signing_preimage_v1(self) -> bytes:
        """Encode the observed signing preimage shape: signature removed, TTL fixed to 0.

        Upstream Android's `toBinaryDataForSigning()` copies the packet with
        `signature = null` and `ttl = SYNC_TTL_HOPS` before passing it through
        `BinaryProtocol.encode(...)`, which may compress and pad. This helper
        mirrors that shape only; it does not sign or validate signatures.
        """

        unsigned = BitchatPacketFixture(
            version=self.version,
            packet_type=self.packet_type,
            ttl=BITCHAT_SYNC_TTL_HOPS,
            timestamp_ms=self.timestamp_ms,
            sender_id=self.sender_id,
            recipient_id=self.recipient_id,
            payload=self.payload,
            signature=None,
            route=self.route,
        )
        return unsigned.encode_wire_v1(apply_padding=True, allow_compression=True)

    def _encode_unpadded_v1(self, *, allow_compression: bool) -> bytes:
        """Encode as raw v1 packet bytes, optionally with compressed payload field."""

        if self.version not in (BITCHAT_PACKET_VERSION_V1, BITCHAT_PACKET_VERSION_V2):
            raise BitchatPacketFixtureError("only v1/v2 fixture packets are supported")
        _validate_byte("packet_type", self.packet_type)
        _validate_byte("ttl", self.ttl)
        if self.timestamp_ms < 0 or self.timestamp_ms > 0xFFFF_FFFF_FFFF_FFFF:
            raise BitchatPacketFixtureError("timestamp_ms must fit uint64")
        if len(self.sender_id) != BITCHAT_SENDER_ID_SIZE:
            raise BitchatPacketFixtureError("sender_id must be exactly 8 bytes")
        payload = self.payload
        original_payload_size: int | None = None
        if allow_compression and should_compress_payload(self.payload):
            compressed = compress_payload_raw_deflate(self.payload)
            if compressed is not None:
                original_payload_size = len(self.payload)
                prefix_size = 4 if self.version >= BITCHAT_PACKET_VERSION_V2 else 2
                payload = original_payload_size.to_bytes(prefix_size, "big") + compressed
        if self.version == BITCHAT_PACKET_VERSION_V1 and len(payload) > 0xFFFF:
            raise BitchatPacketFixtureError("v1 payload must fit uint16 length")
        if self.version == BITCHAT_PACKET_VERSION_V2 and len(payload) > 0xFFFF_FFFF:
            raise BitchatPacketFixtureError("v2 payload must fit uint32 length")
        flags = 0
        if self.recipient_id is not None:
            if len(self.recipient_id) != BITCHAT_RECIPIENT_ID_SIZE:
                raise BitchatPacketFixtureError("recipient_id must be exactly 8 bytes")
            flags |= _FLAG_HAS_RECIPIENT
        if self.signature is not None:
            if len(self.signature) != BITCHAT_SIGNATURE_SIZE:
                raise BitchatPacketFixtureError("signature must be exactly 64 bytes")
            flags |= _FLAG_HAS_SIGNATURE
        if original_payload_size is not None:
            flags |= _FLAG_IS_COMPRESSED
        route_hops: tuple[bytes, ...] = ()
        if self.route:
            if self.version < BITCHAT_PACKET_VERSION_V2:
                raise BitchatPacketFixtureError("route fixtures require packet version 2")
            if len(self.route) > 255:
                raise BitchatPacketFixtureError("route hop count must fit uint8")
            route_hops = tuple(_normalize_peer_id("route hop", hop) for hop in self.route)
            flags |= _FLAG_HAS_ROUTE

        parts = [
            bytes([self.version, self.packet_type, self.ttl]),
            self.timestamp_ms.to_bytes(8, "big"),
            bytes([flags]),
        ]
        if self.version >= BITCHAT_PACKET_VERSION_V2:
            parts.append(len(payload).to_bytes(4, "big"))
        else:
            parts.append(len(payload).to_bytes(2, "big"))
        parts.append(
            self.sender_id,
        )
        if self.recipient_id is not None:
            parts.append(self.recipient_id)
        if route_hops:
            parts.append(bytes([len(route_hops)]))
            parts.extend(route_hops)
        parts.append(payload)
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
    """Decode raw unpadded bitchat v1 packet fixture bytes."""

    return _decode_unpadded_v1_packet_fixture(data)


def decode_wire_v1_packet_fixture(data: bytes) -> BitchatPacketFixture:
    """Decode v1 fixture bytes using the observed raw-first, then-unpad flow."""

    try:
        return _decode_unpadded_v1_packet_fixture(data)
    except BitchatPacketFixtureError as raw_exc:
        unpadded = unpad_fixture_packet(data)
        if unpadded == data:
            raise raw_exc
        return _decode_unpadded_v1_packet_fixture(unpadded)


def _decode_unpadded_v1_packet_fixture(data: bytes) -> BitchatPacketFixture:
    """Decode one unpadded v1/v2 packet, including fixture compressed payloads.

    Compressed fixture payloads use the observed layout: v1 prefixes a 2-byte
    original size, while v2 prefixes a 4-byte original size. The returned
    fixture payload is the decompressed original.
    """

    if len(data) < BITCHAT_HEADER_SIZE_V1 + BITCHAT_SENDER_ID_SIZE:
        raise BitchatPacketFixtureError("packet too short for v1 header and sender")
    version = data[0]
    if version not in (BITCHAT_PACKET_VERSION_V1, BITCHAT_PACKET_VERSION_V2):
        raise BitchatPacketFixtureError("only v1/v2 fixture packets are supported")
    header_size = BITCHAT_HEADER_SIZE_V2 if version >= BITCHAT_PACKET_VERSION_V2 else BITCHAT_HEADER_SIZE_V1
    if len(data) < header_size + BITCHAT_SENDER_ID_SIZE:
        raise BitchatPacketFixtureError("packet too short for header and sender")
    packet_type = data[1]
    ttl = data[2]
    timestamp_ms = int.from_bytes(data[3:11], "big")
    flags = data[11]
    if version == BITCHAT_PACKET_VERSION_V1 and flags & _FLAG_HAS_ROUTE:
        raise BitchatPacketFixtureError("route packets are outside v1 fixture scope")
    if version >= BITCHAT_PACKET_VERSION_V2:
        payload_len = int.from_bytes(data[12:16], "big")
    else:
        payload_len = int.from_bytes(data[12:14], "big")
    offset = header_size
    sender_id = data[offset : offset + BITCHAT_SENDER_ID_SIZE]
    offset += BITCHAT_SENDER_ID_SIZE
    recipient_id = None
    if flags & _FLAG_HAS_RECIPIENT:
        if len(data) < offset + BITCHAT_RECIPIENT_ID_SIZE:
            raise BitchatPacketFixtureError("packet too short for recipient")
        recipient_id = data[offset : offset + BITCHAT_RECIPIENT_ID_SIZE]
        offset += BITCHAT_RECIPIENT_ID_SIZE
    route = None
    if version >= BITCHAT_PACKET_VERSION_V2 and flags & _FLAG_HAS_ROUTE:
        if len(data) < offset + 1:
            raise BitchatPacketFixtureError("packet too short for route count")
        route_count = data[offset]
        offset += 1
        route_hops = []
        for _ in range(route_count):
            if len(data) < offset + BITCHAT_ROUTE_HOP_SIZE:
                raise BitchatPacketFixtureError("packet too short for route hop")
            route_hops.append(data[offset : offset + BITCHAT_ROUTE_HOP_SIZE])
            offset += BITCHAT_ROUTE_HOP_SIZE
        route = tuple(route_hops) if route_hops else None
    if len(data) < offset + payload_len:
        raise BitchatPacketFixtureError("packet too short for payload")
    payload_field = data[offset : offset + payload_len]
    offset += payload_len
    if flags & _FLAG_IS_COMPRESSED:
        length_prefix_size = 4 if version >= BITCHAT_PACKET_VERSION_V2 else 2
        if len(payload_field) < length_prefix_size:
            raise BitchatPacketFixtureError("compressed v1 payload missing original size prefix")
        original_size = int.from_bytes(payload_field[:length_prefix_size], "big")
        compressed_payload = payload_field[length_prefix_size:]
        payload = decompress_payload_raw_deflate(compressed_payload, original_size)
    else:
        payload = payload_field
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
        route=route,
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


@dataclass(frozen=True, slots=True)
class BitchatFragmentPayloadFixture:
    """Observed 13-byte bitchat fragment payload header plus fragment data."""

    fragment_id: bytes
    index: int
    total: int
    original_type: int
    data: bytes

    def encode(self) -> bytes:
        if len(self.fragment_id) != BITCHAT_FRAGMENT_ID_SIZE:
            raise BitchatPacketFixtureError("fragment_id must be exactly 8 bytes")
        if self.index < 0 or self.index > 0xFFFF:
            raise BitchatPacketFixtureError("fragment index must fit uint16")
        if self.total <= 0 or self.total > 0xFFFF:
            raise BitchatPacketFixtureError("fragment total must fit uint16 and be nonzero")
        if self.index >= self.total:
            raise BitchatPacketFixtureError("fragment index must be less than total")
        _validate_byte("original_type", self.original_type)
        if not self.data:
            raise BitchatPacketFixtureError("fragment data must be non-empty")
        return b"".join(
            [
                self.fragment_id,
                self.index.to_bytes(2, "big"),
                self.total.to_bytes(2, "big"),
                bytes([self.original_type]),
                self.data,
            ]
        )


def decode_fragment_payload_fixture(data: bytes) -> BitchatFragmentPayloadFixture:
    """Decode the observed bitchat fragment payload fixture shape."""

    if len(data) < BITCHAT_FRAGMENT_HEADER_SIZE:
        raise BitchatPacketFixtureError("fragment payload too short")
    fragment = BitchatFragmentPayloadFixture(
        fragment_id=data[:BITCHAT_FRAGMENT_ID_SIZE],
        index=int.from_bytes(data[8:10], "big"),
        total=int.from_bytes(data[10:12], "big"),
        original_type=data[12],
        data=data[BITCHAT_FRAGMENT_HEADER_SIZE:],
    )
    fragment.encode()
    return fragment


def make_fragment_packet_fixture(
    *,
    original: BitchatPacketFixture,
    fragment_id: bytes,
    index: int,
    total: int,
    fragment_data: bytes,
    recipient_id: bytes | None = None,
) -> BitchatPacketFixture:
    """Create a fragment packet preserving v2 routing when the original is routed."""

    fragment_payload = BitchatFragmentPayloadFixture(
        fragment_id=fragment_id,
        index=index,
        total=total,
        original_type=original.packet_type,
        data=fragment_data,
    )
    return BitchatPacketFixture(
        version=BITCHAT_PACKET_VERSION_V2 if original.route else BITCHAT_PACKET_VERSION_V1,
        packet_type=BITCHAT_MESSAGE_TYPE_FRAGMENT,
        ttl=original.ttl,
        timestamp_ms=original.timestamp_ms,
        sender_id=original.sender_id,
        recipient_id=recipient_id if recipient_id is not None else original.recipient_id,
        payload=fragment_payload.encode(),
        signature=None,
        route=original.route,
    )


def reassemble_fragment_payload_fixtures(fragments: list[BitchatFragmentPayloadFixture]) -> bytes:
    """Reassemble complete fragment payload fixtures in index order."""

    if not fragments:
        raise BitchatPacketFixtureError("no fragments to reassemble")
    fragment_id = fragments[0].fragment_id
    total = fragments[0].total
    original_type = fragments[0].original_type
    by_index: dict[int, BitchatFragmentPayloadFixture] = {}
    for fragment in fragments:
        fragment.encode()
        if fragment.fragment_id != fragment_id:
            raise BitchatPacketFixtureError("fragment_id mismatch")
        if fragment.total != total or fragment.original_type != original_type:
            raise BitchatPacketFixtureError("fragment metadata mismatch")
        if fragment.index in by_index and by_index[fragment.index].data != fragment.data:
            raise BitchatPacketFixtureError("conflicting duplicate fragment")
        by_index[fragment.index] = fragment
    if set(by_index) != set(range(total)):
        raise BitchatPacketFixtureError("incomplete fragment set")
    return b"".join(by_index[index].data for index in range(total))


def compute_packet_id_fixture(packet: BitchatPacketFixture) -> bytes:
    """Compute observed sync packet ID: SHA-256(type|sender|timestamp|payload)[:16]."""

    digest = hashlib.sha256(
        bytes([packet.packet_type])
        + packet.sender_id
        + packet.timestamp_ms.to_bytes(8, "big")
        + packet.payload
    ).digest()
    return digest[:16]


def compute_packet_id_hex_fixture(packet: BitchatPacketFixture) -> str:
    """Return the observed sync packet ID fixture as lowercase hex."""

    return compute_packet_id_fixture(packet).hex()


def optimal_padding_block_size(data_size: int) -> int:
    """Observed padding block choice: smallest block fitting data plus ~16 bytes."""

    total_size = data_size + 16
    for block_size in BITCHAT_PADDING_BLOCK_SIZES:
        if total_size <= block_size:
            return block_size
    return data_size


def pad_fixture_packet(data: bytes, target_size: int) -> bytes:
    """Apply the observed PKCS#7-style block padding for fixture packets."""

    if len(data) >= target_size:
        return data
    padding_needed = target_size - len(data)
    if padding_needed <= 0 or padding_needed > 255:
        return data
    return data + bytes([padding_needed]) * padding_needed


def unpad_fixture_packet(data: bytes) -> bytes:
    """Remove observed PKCS#7-style padding only when it validates strictly."""

    if not data:
        return data
    padding_length = data[-1]
    if padding_length <= 0 or padding_length > len(data):
        return data
    if data[-padding_length:] != bytes([padding_length]) * padding_length:
        return data
    return data[:-padding_length]


def should_compress_payload(data: bytes) -> bool:
    """Observed compression predicate: threshold plus simple byte-diversity check."""

    if len(data) < BITCHAT_COMPRESSION_THRESHOLD_BYTES:
        return False
    unique_byte_ratio = len(set(data)) / min(len(data), 256)
    return unique_byte_ratio < 0.9


def compress_payload_raw_deflate(data: bytes) -> bytes | None:
    """Compress with raw deflate if beneficial, matching the observed fixture shape."""

    if len(data) < BITCHAT_COMPRESSION_THRESHOLD_BYTES:
        return None
    compressor = zlib.compressobj(level=zlib.Z_DEFAULT_COMPRESSION, wbits=-zlib.MAX_WBITS)
    compressed = compressor.compress(data) + compressor.flush()
    if compressed and len(compressed) < len(data):
        return compressed
    return None


def decompress_payload_raw_deflate(compressed_data: bytes, original_size: int) -> bytes:
    """Decompress raw deflate fixture payloads with basic bomb-ratio protection."""

    if original_size < 0:
        raise BitchatPacketFixtureError("original compressed payload size cannot be negative")
    if compressed_data:
        ratio = original_size / len(compressed_data)
        if ratio > BITCHAT_COMPRESSION_BOMB_RATIO_LIMIT:
            raise BitchatPacketFixtureError("suspicious compression ratio")
    try:
        decompressed = zlib.decompress(compressed_data, wbits=-zlib.MAX_WBITS)
    except zlib.error as raw_exc:
        try:
            decompressed = zlib.decompress(compressed_data)
        except zlib.error as zlib_exc:
            raise BitchatPacketFixtureError("compressed payload could not be decompressed") from zlib_exc
        if not decompressed:
            raise BitchatPacketFixtureError("compressed payload could not be decompressed") from raw_exc
    if len(decompressed) != original_size:
        if not decompressed:
            raise BitchatPacketFixtureError("decompressed payload is empty")
        return decompressed
    return decompressed


def _normalize_peer_id(name: str, value: bytes) -> bytes:
    if len(value) != BITCHAT_ROUTE_HOP_SIZE:
        raise BitchatPacketFixtureError(f"{name} must be exactly 8 bytes")
    return value


def _validate_byte(name: str, value: int) -> None:
    if value < 0 or value > 0xFF:
        raise BitchatPacketFixtureError(f"{name} must fit uint8")
