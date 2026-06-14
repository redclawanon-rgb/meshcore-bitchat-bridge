"""Transport seam for live MeshCore companion datagram adapters.

This module deliberately models companion *bytes*, not BLE, serial, or TCP.
Hardware-specific adapters should implement the same small seam that the fake
transport uses in tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .sim import DeliveredText, SimulatedBridgeNode, SimulatedMeshCoreLink


class CompanionDatagramTransport(Protocol):
    """Minimal byte seam needed by the bridge stack."""

    def send_channel_data_command(self, command: bytes) -> None:
        """Send one MeshCore companion channel-data command."""

    def recv_channel_data_notification(self) -> bytes | None:
        """Receive one MeshCore companion channel-data notification if available."""


@dataclass(slots=True)
class FakeCompanionDatagramTransport:
    """In-memory transport for tests and dry-run bridge orchestration.

    It accepts the same command bytes a live adapter would write to MeshCore and
    queues the same notification bytes a live adapter would read from MeshCore.
    """

    link: SimulatedMeshCoreLink = field(default_factory=SimulatedMeshCoreLink)
    sent_commands: list[bytes] = field(default_factory=list)
    queued_notifications: list[bytes] = field(default_factory=list)

    def send_channel_data_command(self, command: bytes) -> None:
        self.sent_commands.append(command)
        self.queued_notifications.append(self.link.command_to_notification(command))

    def recv_channel_data_notification(self) -> bytes | None:
        if not self.queued_notifications:
            return None
        return self.queued_notifications.pop(0)


def send_text_over_transport(
    sender: SimulatedBridgeNode,
    transport: CompanionDatagramTransport,
    text: str,
) -> int:
    """Encode text and send all resulting companion commands over transport.

    Returns the number of commands sent.
    """
    commands = sender.make_text_commands(text)
    for command in commands:
        transport.send_channel_data_command(command)
    return len(commands)


def drain_transport_to_node(
    transport: CompanionDatagramTransport,
    receiver: SimulatedBridgeNode,
) -> list[DeliveredText]:
    """Drain queued notifications into a receiver node."""
    delivered: list[DeliveredText] = []
    while True:
        raw = transport.recv_channel_data_notification()
        if raw is None:
            break
        maybe = receiver.receive_notification(raw)
        if maybe is not None:
            delivered.append(maybe)
    return delivered
