"""No-hardware serial framing helpers for MeshCore companion bytes.

meshcore_py wraps outgoing serial writes as:

    0x3c + uint16_le(size) + companion_command_bytes

and parses incoming serial frames using:

    0x3e + uint16_le(size) + companion_notification_bytes

This module keeps that byte-level logic testable without opening a serial port.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Protocol

from .bridge_frame import BridgeFrameError

SERIAL_TX_START = 0x3C
SERIAL_RX_START = 0x3E
MAX_SERIAL_PAYLOAD = 300


class SerialByteStream(Protocol):
    """Small serial-like byte stream seam used by the transport skeleton."""

    def write(self, data: bytes) -> object:
        """Write bytes to the underlying stream."""
        ...

    def read(self, size: int = 1) -> bytes:
        """Read up to size bytes from the underlying stream."""
        ...


@dataclass(slots=True)
class InMemorySerialByteStream:
    """Serial-like byte stream for fake-stream transport tests/dry runs.

    It records all bytes written by the transport and allows tests to inject
    synthetic incoming serial bytes without opening or probing any real port.
    """

    incoming: bytearray = field(default_factory=bytearray)
    writes: list[bytes] = field(default_factory=list)

    def write(self, data: bytes) -> int:
        self.writes.append(data)
        return len(data)

    def read(self, size: int = 1) -> bytes:
        if not self.incoming:
            return b""
        chunk = bytes(self.incoming[:size])
        del self.incoming[:size]
        return chunk

    def inject(self, data: bytes) -> None:
        """Queue raw incoming serial bytes for future reads."""
        self.incoming.extend(data)

    def inject_notification(self, notification: bytes) -> None:
        """Queue one companion notification wrapped as a serial RX packet."""
        self.inject(wrap_serial_rx_packet(notification))


def wrap_serial_tx_packet(command: bytes) -> bytes:
    """Wrap companion command bytes for serial write to a MeshCore device."""
    if len(command) > MAX_SERIAL_PAYLOAD:
        raise BridgeFrameError(
            f"serial payload too large: {len(command)} > {MAX_SERIAL_PAYLOAD}"
        )
    return bytes([SERIAL_TX_START]) + len(command).to_bytes(2, "little") + command


def unwrap_serial_tx_packet(packet: bytes) -> bytes:
    """Extract companion command bytes from a dry-run serial TX packet.

    This is intentionally a no-hardware replay helper: it accepts bytes already
    emitted by the dry-run path and validates the MeshCore serial-write envelope
    without opening or probing any serial port.
    """
    if len(packet) < 3:
        raise BridgeFrameError(f"serial TX packet too short: {len(packet)} < 3")
    if packet[0] != SERIAL_TX_START:
        raise BridgeFrameError(f"unexpected serial TX start: 0x{packet[0]:02x}")
    size = int.from_bytes(packet[1:3], "little")
    if size > MAX_SERIAL_PAYLOAD:
        raise BridgeFrameError(
            f"serial payload too large: {size} > {MAX_SERIAL_PAYLOAD}"
        )
    actual = len(packet) - 3
    if actual != size:
        raise BridgeFrameError(f"serial TX payload length mismatch: {actual} != {size}")
    return packet[3:]


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


@dataclass(slots=True)
class SerialCompanionDatagramTransport:
    """Serial implementation skeleton for the companion datagram seam.

    The default constructor is intentionally no-open: importing or instantiating
    this class does not import pyserial and does not touch a real port. Tests and
    dry-runs can pass a fake serial-like ``byte_stream`` with ``read``/``write``.
    Opening a real port requires ``open_real_port=True``.
    """

    port: str = "/dev/ttyUSB0"
    baud: int = 115200
    open_real_port: bool = False
    byte_stream: SerialByteStream | None = None
    serial_factory: object | None = None
    read_size: int = 1024
    rx_reader: SerialRxPacketReader = field(default_factory=SerialRxPacketReader)
    sent_packets: list[bytes] = field(default_factory=list)
    queued_notifications: list[bytes] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.byte_stream is not None:
            return
        if not self.open_real_port:
            return

        factory = self.serial_factory
        if factory is None:
            try:
                factory = import_module("serial").Serial
            except ModuleNotFoundError as exc:  # pragma: no cover - env dependent
                raise RuntimeError(
                    "pyserial is required to open a real serial port; install it "
                    "or instantiate with open_real_port=False/fake byte_stream"
                ) from exc
        self.byte_stream = factory(self.port, self.baud, timeout=0)  # type: ignore[misc, operator]

    def send_channel_data_command(self, command: bytes) -> None:
        """Wrap and send one companion command as a MeshCore serial TX packet."""
        packet = wrap_serial_tx_packet(command)
        self.sent_packets.append(packet)
        if self.byte_stream is not None:
            self.byte_stream.write(packet)

    def recv_channel_data_notification(self) -> bytes | None:
        """Read and unwrap one companion notification if a complete packet exists."""
        if self.queued_notifications:
            return self.queued_notifications.pop(0)
        if self.byte_stream is not None:
            chunk = self.byte_stream.read(self.read_size)
            if chunk:
                packets = self.rx_reader.feed(chunk)
                if packets:
                    self.queued_notifications.extend(packets[1:])
                    return packets[0]
        packets = self.rx_reader.feed(b"")
        if not packets:
            return None
        self.queued_notifications.extend(packets[1:])
        return packets[0]
