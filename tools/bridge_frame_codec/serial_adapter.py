"""No-hardware serial framing helpers for MeshCore companion bytes.

meshcore_py wraps outgoing serial writes as:

    0x3c + uint16_le(size) + companion_command_bytes

and parses incoming serial frames using:

    0x3e + uint16_le(size) + companion_notification_bytes

This module keeps that byte-level logic testable without opening a serial port.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .bridge_frame import BridgeFrameError

SERIAL_TX_START = 0x3C
SERIAL_RX_START = 0x3E
MAX_SERIAL_PAYLOAD = 300


def wrap_serial_tx_packet(command: bytes) -> bytes:
    """Wrap companion command bytes for serial write to a MeshCore device."""
    if len(command) > MAX_SERIAL_PAYLOAD:
        raise BridgeFrameError(
            f"serial payload too large: {len(command)} > {MAX_SERIAL_PAYLOAD}"
        )
    return bytes([SERIAL_TX_START]) + len(command).to_bytes(2, "little") + command


def wrap_serial_rx_packet(notification: bytes) -> bytes:
    """Build a synthetic incoming serial packet for tests/dry runs."""
    if len(notification) > MAX_SERIAL_PAYLOAD:
        raise BridgeFrameError(
            f"serial payload too large: {len(notification)} > {MAX_SERIAL_PAYLOAD}"
        )
    return bytes([SERIAL_RX_START]) + len(notification).to_bytes(2, "little") + notification


@dataclass(slots=True)
class SerialRxPacketReader:
    """Incremental parser for incoming MeshCore serial packets.

    It mirrors the upstream behavior enough for bridge tests: discard bytes before
    the RX start marker, wait for a 3-byte header, validate size, then emit the
    companion notification payload.
    """

    buffer: bytearray = field(default_factory=bytearray)

    def feed(self, data: bytes) -> list[bytes]:
        self.buffer.extend(data)
        packets: list[bytes] = []
        while True:
            start = self.buffer.find(bytes([SERIAL_RX_START]))
            if start < 0:
                self.buffer.clear()
                return packets
            if start > 0:
                del self.buffer[:start]
            if len(self.buffer) < 3:
                return packets
            size = int.from_bytes(self.buffer[1:3], "little")
            if size > MAX_SERIAL_PAYLOAD:
                # Drop invalid marker and keep scanning the remainder.
                del self.buffer[0]
                continue
            total = 3 + size
            if len(self.buffer) < total:
                return packets
            packets.append(bytes(self.buffer[3:total]))
            del self.buffer[:total]
