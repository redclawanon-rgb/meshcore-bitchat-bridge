#!/usr/bin/env python3
"""No-hardware bridge pump demo CLI.

This smoke demo wires only fake/local components: a fake MeshCore companion
transport, simulated bridge nodes, and the semantic fake bitchat text carrier.
It never opens serial/BLE and does not model or claim stock bitchat packet
compatibility.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

try:
    from bridge_frame_codec import (
        FakeBitchatTextCarrier,
        FakeCompanionDatagramTransport,
        SimulatedBridgeNode,
        drain_transport_to_node,
        pump_text_bridge_once,
        send_text_over_transport,
    )
except ModuleNotFoundError:  # imported as tools.bridge_pump_demo from tests
    from tools.bridge_frame_codec import (
        FakeBitchatTextCarrier,
        FakeCompanionDatagramTransport,
        SimulatedBridgeNode,
        drain_transport_to_node,
        pump_text_bridge_once,
        send_text_over_transport,
    )


def _published_messages(carrier: FakeBitchatTextCarrier) -> list[dict[str, object]]:
    return [
        {
            "from_bridge_id": f"0x{item.from_bridge_id:08x}",
            "message_id": item.message_id,
            "text": item.text,
        }
        for item in carrier.published_texts
    ]


def _delivered_messages(node: SimulatedBridgeNode) -> list[dict[str, object]]:
    return [
        {
            "from_bridge_id": f"0x{item.from_bridge_id:08x}",
            "message_id": item.message_id,
            "text": item.text,
        }
        for item in node.inbox
    ]


def run_demo(args: argparse.Namespace) -> dict[str, object]:
    mesh_sender = SimulatedBridgeNode(
        bridge_id=int(args.mesh_sender_id, 0),
        channel_index=args.channel,
    )
    bridge_node = SimulatedBridgeNode(
        bridge_id=int(args.bridge_id, 0),
        channel_index=args.channel,
    )
    mesh_receiver = SimulatedBridgeNode(
        bridge_id=int(args.mesh_receiver_id, 0),
        channel_index=args.channel,
    )
    transport = FakeCompanionDatagramTransport()
    carrier = FakeBitchatTextCarrier()

    seeded_meshcore_commands = send_text_over_transport(
        mesh_sender,
        transport,
        args.meshcore_text,
    )
    carrier.queue_public_text(
        args.bitchat_text,
        carrier_message_id=args.carrier_message_id,
    )

    result = pump_text_bridge_once(
        mesh_node=bridge_node,
        mesh_transport=transport,
        bitchat_carrier=carrier,
    )
    receiver_delivered = drain_transport_to_node(transport, mesh_receiver)

    return {
        "type": "meshcore_bitchat_bridge_pump_demo_v0",
        "mode": "no-hardware",
        "safety": {
            "opens_ble": False,
            "opens_serial": False,
            "stock_bitchat_compatibility": "not-claimed",
            "uses_fake_bitchat_text_carrier": True,
            "uses_fake_meshcore_transport": True,
        },
        "channel_index": args.channel,
        "seeded": {
            "meshcore_commands": seeded_meshcore_commands,
            "bitchat_public_texts": 1,
        },
        "pump_counts": {
            "meshcore_notifications_delivered": result.meshcore_notifications_delivered,
            "meshcore_texts_published": result.meshcore_texts_published,
            "bitchat_texts_forwarded": result.bitchat_texts_forwarded,
            "meshcore_commands_sent": result.meshcore_commands_sent,
        },
        "carrier": {
            "published_count": len(carrier.published_texts),
            "published_messages": _published_messages(carrier),
            "queued_public_texts_remaining": len(carrier.queued_public_texts),
        },
        "receiver": {
            "delivered_count": len(receiver_delivered),
            "inbox": _delivered_messages(mesh_receiver),
            "inbox_texts": [item.text for item in mesh_receiver.inbox],
        },
        "transport": {
            "sent_command_count": len(transport.sent_commands),
            "sent_command_lengths": [len(command) for command in transport.sent_commands],
            "queued_notifications_remaining": len(transport.queued_notifications),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MeshCore/bitchat bridge pump no-hardware smoke demo"
    )
    parser.add_argument("--mesh-sender-id", default="0x000000a1", help="decimal or 0x-prefixed uint32")
    parser.add_argument("--bridge-id", default="0x000000b2", help="decimal or 0x-prefixed uint32")
    parser.add_argument("--mesh-receiver-id", default="0x000000c3", help="decimal or 0x-prefixed uint32")
    parser.add_argument("--channel", type=int, default=1, help="MeshCore channel index")
    parser.add_argument("--meshcore-text", default="meshcore public text into fake carrier")
    parser.add_argument("--bitchat-text", default="fake carrier public text into meshcore")
    parser.add_argument("--carrier-message-id", default="fake-carrier-1")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run_demo(args), indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - exercised by smoke/CLI use
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
