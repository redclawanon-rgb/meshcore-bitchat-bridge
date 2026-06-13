"""Bridge frame v0 codec.

The frame is designed to fit MeshCore companion channel data datagrams:
163 bytes carrier budget, 23 bytes fixed bridge overhead, 140 bytes payload.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

MAGIC = b"BB"
VERSION = 0
MAX_CARRIER_PAYLOAD = 163
FIXED_OVERHEAD = 22
MAX_FRAME_PAYLOAD = MAX_CARRIER_PAYLOAD - FIXED_OVERHEAD

MSG_HELLO = 0x01
MSG_TEXT_FRAGMENT = 0x02
MSG_ACK = 0x03
MSG_NACK = 0x04
MSG_PEER_ADVERT = 0x05


class BridgeFrameError(ValueError):
    """Raised when a bridge frame is invalid."""


@dataclass(frozen=True, slots=True)
class BridgeFrame:
    flags: int
    msg_type: int
    bridge_id: int
    message_id: int
    fragment_index: int
    fragment_count: int
    payload: bytes
    version: int = VERSION

    def validate(self) -> None:
        if self.version != VERSION:
            raise BridgeFrameError(f"unsupported version: {self.version}")
        for name, value, upper in [
            ("flags", self.flags, 0xFF),
            ("msg_type", self.msg_type, 0xFF),
            ("bridge_id", self.bridge_id, 0xFFFFFFFF),
            ("message_id", self.message_id, 0xFFFFFFFFFFFFFFFF),
            ("fragment_index", self.fragment_index, 0xFF),
            ("fragment_count", self.fragment_count, 0xFF),
        ]:
            if not 0 <= value <= upper:
                raise BridgeFrameError(f"{name} out of range: {value}")
        if self.fragment_count == 0:
            raise BridgeFrameError("fragment_count must be 1..255")
        if self.fragment_index >= self.fragment_count:
            raise BridgeFrameError("fragment_index must be less than fragment_count")
        if len(self.payload) > MAX_FRAME_PAYLOAD:
            raise BridgeFrameError(
                f"payload too large: {len(self.payload)} > {MAX_FRAME_PAYLOAD}"
            )


def crc16_xmodem(data: bytes) -> int:
    """CRC-16/XMODEM: poly 0x1021, init 0x0000."""
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def encode_frame(frame: BridgeFrame) -> bytes:
    """Encode a bridge frame to bytes, including CRC."""
    frame.validate()
    header = bytearray()
    header += MAGIC
    header.append(frame.version)
    header.append(frame.flags)
    header.append(frame.msg_type)
    header += frame.bridge_id.to_bytes(4, "little")
    header += frame.message_id.to_bytes(8, "little")
    header.append(frame.fragment_index)
    header.append(frame.fragment_count)
    header.append(len(frame.payload))
    body = bytes(header) + frame.payload
    crc = crc16_xmodem(body)
    return body + crc.to_bytes(2, "little")


def decode_frame(raw: bytes) -> BridgeFrame:
    """Decode and validate a bridge frame from bytes."""
    if len(raw) < FIXED_OVERHEAD:
        raise BridgeFrameError(f"frame too short: {len(raw)} < {FIXED_OVERHEAD}")
    if raw[:2] != MAGIC:
        raise BridgeFrameError("bad magic")
    version = raw[2]
    if version != VERSION:
        raise BridgeFrameError(f"unsupported version: {version}")
    payload_len = raw[19]
    if payload_len > MAX_FRAME_PAYLOAD:
        raise BridgeFrameError(
            f"payload too large: {payload_len} > {MAX_FRAME_PAYLOAD}"
        )
    expected_len = 20 + payload_len + 2
    if len(raw) != expected_len:
        raise BridgeFrameError(f"length mismatch: got {len(raw)}, expected {expected_len}")
    expected_crc = int.from_bytes(raw[-2:], "little")
    actual_crc = crc16_xmodem(raw[:-2])
    if actual_crc != expected_crc:
        raise BridgeFrameError(
            f"crc mismatch: got 0x{expected_crc:04x}, expected 0x{actual_crc:04x}"
        )
    frame = BridgeFrame(
        version=version,
        flags=raw[3],
        msg_type=raw[4],
        bridge_id=int.from_bytes(raw[5:9], "little"),
        message_id=int.from_bytes(raw[9:17], "little"),
        fragment_index=raw[17],
        fragment_count=raw[18],
        payload=raw[20:-2],
    )
    frame.validate()
    return frame


def fragment_payload(
    payload: bytes,
    *,
    flags: int,
    msg_type: int,
    bridge_id: int,
    message_id: int,
) -> list[BridgeFrame]:
    """Split payload into bridge frames."""
    if len(payload) == 0:
        chunks = [b""]
    else:
        chunks = [
            payload[i : i + MAX_FRAME_PAYLOAD]
            for i in range(0, len(payload), MAX_FRAME_PAYLOAD)
        ]
    if len(chunks) > 255:
        raise BridgeFrameError(f"too many fragments: {len(chunks)} > 255")
    return [
        BridgeFrame(
            flags=flags,
            msg_type=msg_type,
            bridge_id=bridge_id,
            message_id=message_id,
            fragment_index=index,
            fragment_count=len(chunks),
            payload=chunk,
        )
        for index, chunk in enumerate(chunks)
    ]


def reassemble_fragments(frames: Iterable[BridgeFrame]) -> bytes:
    """Reassemble frames for one `(bridge_id, message_id, msg_type)` tuple."""
    frames = list(frames)
    if not frames:
        raise BridgeFrameError("no fragments")
    first = frames[0]
    key = (first.bridge_id, first.message_id, first.msg_type)
    count = first.fragment_count
    slots: list[bytes | None] = [None] * count
    for frame in frames:
        frame.validate()
        if (frame.bridge_id, frame.message_id, frame.msg_type) != key:
            raise BridgeFrameError("mixed fragment keys")
        if frame.fragment_count != count:
            raise BridgeFrameError("conflicting fragment_count")
        existing = slots[frame.fragment_index]
        if existing is not None and existing != frame.payload:
            raise BridgeFrameError("conflicting duplicate fragment")
        slots[frame.fragment_index] = frame.payload
    missing = [str(i) for i, payload in enumerate(slots) if payload is None]
    if missing:
        raise BridgeFrameError(f"missing fragments: {', '.join(missing)}")
    return b"".join(payload for payload in slots if payload is not None)
