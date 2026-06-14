"""No-hardware text bridge pump between MeshCore-delivered text and bitchat carrier.

The helper in this module is intentionally tiny and local-only: it moves decoded
``DeliveredText`` objects into a semantic ``BitchatTextCarrier`` and moves
carrier-originated public text into the existing MeshCore transport-neutral send
path. It does not open serial ports, speak BLE, forge stock bitchat packets, or
handle anything other than public text.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bitchat_app_adapter import BitchatAppAdapter
from .bitchat_text import BitchatTextCarrier
from .sim import SimulatedBridgeNode
from .transport import (
    CompanionDatagramTransport,
    drain_transport_to_node,
    send_text_over_transport,
)


@dataclass(frozen=True, slots=True)
class BridgePumpResult:
    """Summary of one local text bridge pump pass."""

    meshcore_notifications_delivered: int = 0
    meshcore_texts_published: int = 0
    bitchat_texts_forwarded: int = 0
    meshcore_commands_sent: int = 0


@dataclass(frozen=True, slots=True)
class AppAdapterBridgePumpResult:
    """Summary of one local app-adapter bridge pump pass."""

    meshcore_notifications_delivered: int = 0
    meshcore_texts_published_to_app: int = 0
    bitchat_packets_ingested: int = 0
    bitchat_public_events_forwarded: int = 0
    meshcore_commands_sent: int = 0


def pump_text_bridge_once(
    *,
    mesh_node: SimulatedBridgeNode,
    mesh_transport: CompanionDatagramTransport,
    bitchat_carrier: BitchatTextCarrier,
) -> BridgePumpResult:
    """Run one no-hardware public-text bridge pump pass.

    The pass performs three deterministic steps:

    1. Drain queued MeshCore companion notifications from ``mesh_transport`` into
       ``mesh_node`` using ``drain_transport_to_node``.
    2. Drain all ``DeliveredText`` currently in ``mesh_node.inbox`` and publish
       each item to ``bitchat_carrier.publish_public_text``.
    3. Drain carrier-originated public text from
       ``bitchat_carrier.recv_public_text`` and forward each item to MeshCore
       with ``send_text_over_transport``.

    The helper is text-only and transport-neutral. With the fake transport, any
    commands sent in step 3 become queued notifications for a later pump/read;
    they are not re-drained in the same pass.
    """

    delivered = drain_transport_to_node(mesh_transport, mesh_node)

    meshcore_texts_published = 0
    while mesh_node.inbox:
        item = mesh_node.inbox.pop(0)
        bitchat_carrier.publish_public_text(
            item.text,
            from_bridge_id=item.from_bridge_id,
            message_id=item.message_id,
        )
        meshcore_texts_published += 1

    bitchat_texts_forwarded = 0
    meshcore_commands_sent = 0
    while True:
        outbound = bitchat_carrier.recv_public_text()
        if outbound is None:
            break
        meshcore_commands_sent += send_text_over_transport(
            mesh_node,
            mesh_transport,
            outbound.text,
        )
        bitchat_texts_forwarded += 1

    return BridgePumpResult(
        meshcore_notifications_delivered=len(delivered),
        meshcore_texts_published=meshcore_texts_published,
        bitchat_texts_forwarded=bitchat_texts_forwarded,
        meshcore_commands_sent=meshcore_commands_sent,
    )


def pump_app_adapter_bridge_once(
    *,
    mesh_node: SimulatedBridgeNode,
    mesh_transport: CompanionDatagramTransport,
    bitchat_adapter: BitchatAppAdapter,
    inbound_bitchat_packets: list[bytes] | tuple[bytes, ...] = (),
) -> AppAdapterBridgePumpResult:
    """Run one no-hardware bridge pump pass through the app-adapter seam.

    The pass performs three deterministic steps:

    1. Drain queued MeshCore companion notifications from ``mesh_transport`` into
       ``mesh_node``.
    2. Publish decoded ``DeliveredText`` items into ``bitchat_adapter`` using
       ``publish_bridge_text``.
    3. Ingest fixture-backed app/native packet bytes through
       ``bitchat_adapter.ingest_packet_bytes`` and forward each resulting public
       text event to MeshCore with ``send_text_over_transport``.

    This is still a local, fixture-only integration seam. It does not open BLE,
    serial ports, mobile apps, hardware, or stock bitchat sessions.
    """

    delivered = drain_transport_to_node(mesh_transport, mesh_node)

    meshcore_texts_published_to_app = 0
    while mesh_node.inbox:
        item = mesh_node.inbox.pop(0)
        bitchat_adapter.publish_bridge_text(
            item.text,
            from_bridge_id=item.from_bridge_id,
            message_id=item.message_id,
        )
        meshcore_texts_published_to_app += 1

    bitchat_public_events_forwarded = 0
    meshcore_commands_sent = 0
    for packet_bytes in inbound_bitchat_packets:
        events = bitchat_adapter.ingest_packet_bytes(packet_bytes)
        for event in events:
            meshcore_commands_sent += send_text_over_transport(
                mesh_node,
                mesh_transport,
                event.text,
            )
            bitchat_public_events_forwarded += 1

    return AppAdapterBridgePumpResult(
        meshcore_notifications_delivered=len(delivered),
        meshcore_texts_published_to_app=meshcore_texts_published_to_app,
        bitchat_packets_ingested=len(inbound_bitchat_packets),
        bitchat_public_events_forwarded=bitchat_public_events_forwarded,
        meshcore_commands_sent=meshcore_commands_sent,
    )
