"""Deterministic bitchat identity/signature fixtures for adapter research.

These helpers mirror upstream-observed Ed25519 signing and announce-binding byte
shapes using non-secret deterministic test keys. They are for local conformance
fixtures only. They do not load device identity, establish trust, run Noise,
open BLE, or claim stock bitchat interoperability.
"""

from __future__ import annotations

from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

from .bitchat_packet_fixture import BITCHAT_MESSAGE_TYPE_MESSAGE, BitchatPacketFixture

ANNOUNCE_CONTEXT_V1 = b"bitchat-announce-v1"
IDENTITY_TLV_NICKNAME = 0x01
IDENTITY_TLV_NOISE_PUBLIC_KEY = 0x02
IDENTITY_TLV_SIGNING_PUBLIC_KEY = 0x03
IDENTITY_TLV_DIRECT_NEIGHBORS = 0x04


@dataclass(frozen=True, slots=True)
class IdentityAnnouncementFixture:
    """Decoded identity announcement TLV fixture."""

    nickname: str
    noise_public_key: bytes
    signing_public_key: bytes
    direct_neighbors: tuple[bytes, ...] = ()


@dataclass(frozen=True, slots=True)
class VerifiedPublicTextFixture:
    """Accepted signed public text fixture result."""

    peer_id: bytes
    nickname: str
    text: str


class BitchatIdentityFixtureError(ValueError):
    """Raised when a deterministic identity fixture is malformed."""


def ed25519_private_key_from_seed(seed: bytes) -> Ed25519PrivateKey:
    """Create a deterministic Ed25519 private key from a 32-byte test seed."""

    if len(seed) != 32:
        raise BitchatIdentityFixtureError("Ed25519 seed must be exactly 32 bytes")
    return Ed25519PrivateKey.from_private_bytes(seed)


def ed25519_public_key_bytes_from_seed(seed: bytes) -> bytes:
    """Return raw 32-byte Ed25519 public key bytes for a deterministic seed."""

    return ed25519_public_key_bytes(ed25519_private_key_from_seed(seed).public_key())


def ed25519_private_seed_bytes(private_key: Ed25519PrivateKey) -> bytes:
    """Return raw 32-byte private seed bytes, matching upstream key persistence shape."""

    return private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())


def ed25519_public_key_bytes(public_key: Ed25519PublicKey) -> bytes:
    """Return raw 32-byte Ed25519 public key bytes."""

    return public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)


def ed25519_sign_fixture(data: bytes, seed: bytes) -> bytes:
    """Sign fixture bytes with a deterministic non-secret Ed25519 seed."""

    return ed25519_private_key_from_seed(seed).sign(data)


def ed25519_verify_fixture(signature: bytes, data: bytes, public_key_bytes: bytes) -> bool:
    """Verify an Ed25519 fixture signature against raw 32-byte public key bytes."""

    if len(public_key_bytes) != 32:
        raise BitchatIdentityFixtureError("Ed25519 public key must be exactly 32 bytes")
    try:
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(signature, data)
    except InvalidSignature:
        return False
    return True


def canonical_announce_bytes(
    *,
    peer_id: bytes,
    noise_public_key: bytes,
    signing_public_key: bytes,
    nickname: str,
    timestamp_ms: int,
) -> bytes:
    """Build the upstream-observed canonical announce binding bytes.

    Mirrors iOS `canonicalAnnounceBytes(...)`:
    context length + context, 8-byte peer ID padded/truncated, 32-byte Noise key
    padded/truncated, 32-byte Ed25519 public key padded/truncated, nickname
    length + nickname prefix, then uint64 big-endian timestamp milliseconds.
    """

    if timestamp_ms < 0 or timestamp_ms > 0xFFFF_FFFF_FFFF_FFFF:
        raise BitchatIdentityFixtureError("timestamp_ms must fit uint64")
    nickname_bytes = nickname.encode("utf-8")
    out = bytearray()
    out.append(min(len(ANNOUNCE_CONTEXT_V1), 255))
    out.extend(ANNOUNCE_CONTEXT_V1[:255])
    out.extend(_pad_or_truncate(peer_id, 8))
    out.extend(_pad_or_truncate(noise_public_key, 32))
    out.extend(_pad_or_truncate(signing_public_key, 32))
    out.append(min(len(nickname_bytes), 255))
    out.extend(nickname_bytes[:255])
    out.extend(timestamp_ms.to_bytes(8, "big"))
    return bytes(out)


def encode_identity_announcement_tlv(
    *,
    nickname: str,
    noise_public_key: bytes,
    signing_public_key: bytes,
    direct_neighbors: list[bytes] | None = None,
) -> bytes:
    """Encode the observed identity announcement TLV fields for fixtures."""

    nickname_bytes = nickname.encode("utf-8")
    _ensure_tlv_value("nickname", nickname_bytes)
    _ensure_tlv_value("noise_public_key", noise_public_key)
    _ensure_tlv_value("signing_public_key", signing_public_key)
    out = bytearray()
    _append_tlv(out, IDENTITY_TLV_NICKNAME, nickname_bytes)
    _append_tlv(out, IDENTITY_TLV_NOISE_PUBLIC_KEY, noise_public_key)
    _append_tlv(out, IDENTITY_TLV_SIGNING_PUBLIC_KEY, signing_public_key)
    if direct_neighbors:
        neighbors = b"".join(_pad_or_truncate(neighbor, 8) for neighbor in direct_neighbors[:10])
        if neighbors:
            _append_tlv(out, IDENTITY_TLV_DIRECT_NEIGHBORS, neighbors)
    return bytes(out)


def decode_identity_announcement_tlv(data: bytes) -> IdentityAnnouncementFixture:
    """Decode the observed identity announcement TLV fields for fixtures."""

    offset = 0
    nickname: str | None = None
    noise_public_key: bytes | None = None
    signing_public_key: bytes | None = None
    direct_neighbors: tuple[bytes, ...] = ()
    while offset + 2 <= len(data):
        tlv_type = data[offset]
        offset += 1
        length = data[offset]
        offset += 1
        if offset + length > len(data):
            raise BitchatIdentityFixtureError("identity announcement TLV length exceeds payload")
        value = data[offset : offset + length]
        offset += length
        if tlv_type == IDENTITY_TLV_NICKNAME:
            try:
                nickname = value.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise BitchatIdentityFixtureError("identity announcement nickname is not UTF-8") from exc
        elif tlv_type == IDENTITY_TLV_NOISE_PUBLIC_KEY:
            noise_public_key = value
        elif tlv_type == IDENTITY_TLV_SIGNING_PUBLIC_KEY:
            signing_public_key = value
        elif tlv_type == IDENTITY_TLV_DIRECT_NEIGHBORS:
            if len(value) % 8 != 0:
                raise BitchatIdentityFixtureError("direct-neighbor TLV length must be a multiple of 8")
            direct_neighbors = tuple(value[index : index + 8] for index in range(0, len(value), 8))
        else:
            continue
    if offset != len(data):
        raise BitchatIdentityFixtureError("trailing partial identity announcement TLV")
    if nickname is None or noise_public_key is None or signing_public_key is None:
        raise BitchatIdentityFixtureError("identity announcement missing required TLV field")
    if len(signing_public_key) != 32:
        raise BitchatIdentityFixtureError("identity announcement signing public key must be 32 bytes")
    return IdentityAnnouncementFixture(
        nickname=nickname,
        noise_public_key=noise_public_key,
        signing_public_key=signing_public_key,
        direct_neighbors=direct_neighbors,
    )


def sign_packet_fixture(packet: BitchatPacketFixture, seed: bytes) -> BitchatPacketFixture:
    """Attach an Ed25519 signature over the observed packet signing preimage."""

    return BitchatPacketFixture(
        version=packet.version,
        packet_type=packet.packet_type,
        ttl=packet.ttl,
        timestamp_ms=packet.timestamp_ms,
        sender_id=packet.sender_id,
        recipient_id=packet.recipient_id,
        payload=packet.payload,
        signature=ed25519_sign_fixture(packet.encode_signing_preimage_v1(), seed),
    )


class VerifiedSenderFixtureRegistry:
    """Local-only simulation of announce-gated signed public-message acceptance.

    This intentionally models just the byte/signature acceptance seam observed in
    upstream code: a signed identity announce stores a peer's signing public key,
    and later public messages from that peer must carry a valid Ed25519 signature
    over their `toBinaryDataForSigning()` bytes. It does not model BLE, Noise,
    lifecycle timing, persistence, key mismatch policy beyond rejection, or stock
    app compatibility.
    """

    def __init__(self) -> None:
        self._peers: dict[bytes, IdentityAnnouncementFixture] = {}

    def verify_and_register_announce(self, packet: BitchatPacketFixture) -> IdentityAnnouncementFixture:
        announcement = decode_identity_announcement_tlv(packet.payload)
        if packet.signature is None:
            raise BitchatIdentityFixtureError("signed announce is required before registering peer")
        if not ed25519_verify_fixture(
            packet.signature,
            packet.encode_signing_preimage_v1(),
            announcement.signing_public_key,
        ):
            raise BitchatIdentityFixtureError("identity announce signature did not verify")
        existing = self._peers.get(packet.sender_id)
        if existing is not None and existing.noise_public_key != announcement.noise_public_key:
            raise BitchatIdentityFixtureError("identity announce noise key mismatch for peer")
        self._peers[packet.sender_id] = announcement
        return announcement

    def verified_public_text(self, packet: BitchatPacketFixture) -> VerifiedPublicTextFixture:
        if packet.packet_type != BITCHAT_MESSAGE_TYPE_MESSAGE:
            raise BitchatIdentityFixtureError("only public MESSAGE packets are accepted by this fixture")
        if packet.signature is None:
            raise BitchatIdentityFixtureError("signed public message is required")
        announcement = self._peers.get(packet.sender_id)
        if announcement is None:
            raise BitchatIdentityFixtureError("public message sender has no verified announce")
        if not ed25519_verify_fixture(
            packet.signature,
            packet.encode_signing_preimage_v1(),
            announcement.signing_public_key,
        ):
            raise BitchatIdentityFixtureError("public message signature did not verify for registered sender")
        return VerifiedPublicTextFixture(
            peer_id=packet.sender_id,
            nickname=announcement.nickname,
            text=packet.public_text,
        )


def _append_tlv(out: bytearray, tlv_type: int, value: bytes) -> None:
    _ensure_tlv_value("tlv", value)
    out.append(tlv_type)
    out.append(len(value))
    out.extend(value)


def _ensure_tlv_value(name: str, value: bytes) -> None:
    if len(value) > 255:
        raise BitchatIdentityFixtureError(f"{name} TLV value must be <=255 bytes")


def _pad_or_truncate(data: bytes, size: int) -> bytes:
    clipped = data[:size]
    if len(clipped) < size:
        return clipped + bytes(size - len(clipped))
    return clipped
