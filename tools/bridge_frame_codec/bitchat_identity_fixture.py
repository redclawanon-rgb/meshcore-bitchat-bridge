"""Deterministic bitchat identity/signature fixtures for adapter research.

These helpers mirror upstream-observed Ed25519 signing and announce-binding byte
shapes using non-secret deterministic test keys. They are for local conformance
fixtures only. They do not load device identity, establish trust, run Noise,
open BLE, or claim stock bitchat interoperability.
"""

from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

ANNOUNCE_CONTEXT_V1 = b"bitchat-announce-v1"
IDENTITY_TLV_NICKNAME = 0x01
IDENTITY_TLV_NOISE_PUBLIC_KEY = 0x02
IDENTITY_TLV_SIGNING_PUBLIC_KEY = 0x03
IDENTITY_TLV_DIRECT_NEIGHBORS = 0x04


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
