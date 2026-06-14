#!/usr/bin/env python3
"""No-hardware demo CLI for the MeshCore/bitchat bridge simulator."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

try:
    from bridge_frame_codec import SimulatedBridgeNode, SimulatedMeshCoreLink
except ModuleNotFoundError:  # imported as tools.bridge_sim from tests
    from tools.bridge_frame_codec import SimulatedBridgeNode, SimulatedMeshCoreLink


def _send_with_summary(
    *,
    sender_name: str,
    receiver_name: str,
    sender: SimulatedBridgeNode,
    receiver: SimulatedBridgeNode,
    link: SimulatedMeshCoreLink,
    text: str,
) -> dict[str, object]:
    commands = sender.make_text_commands(text)
    delivered = []
    notification_count = 0
    for command in commands:
        notification_count += 1
        maybe = receiver.receive_notification(link.command_to_notification(command))
        if maybe is not None:
            delivered.append(maybe)
    return {
        "from": sender_name,
        "to": receiver_name,
        "text_bytes": len(text.encode("utf-8")),
        "command_count": len(commands),
        "notification_count": notification_count,
        "delivered_count": len(delivered),
        "delivered": [
            {
                "from_bridge_id": f"0x{item.from_bridge_id:08x}",
                "message_id": item.message_id,
                "text": item.text,
            }
            for item in delivered
        ],
    }


def run_demo(args: argparse.Namespace) -> dict[str, object]:
    alice = SimulatedBridgeNode(bridge_id=int(args.alice_id, 0), channel_index=args.channel)
    bob = SimulatedBridgeNode(bridge_id=int(args.bob_id, 0), channel_index=args.channel)
    link = SimulatedMeshCoreLink(snr_scaled=args.snr_scaled)

    exchanges = [
        _send_with_summary(
            sender_name="alice",
            receiver_name="bob",
            sender=alice,
            receiver=bob,
            link=link,
            text=args.alice_text,
        )
    ]
    if args.bob_text is not None:
        exchanges.append(
            _send_with_summary(
                sender_name="bob",
                receiver_name="alice",
                sender=bob,
                receiver=alice,
                link=link,
                text=args.bob_text,
            )
        )

    return {
        "type": "meshcore_bitchat_bridge_sim_v0",
        "mode": "no-hardware",
        "channel_index": args.channel,
        "snr_db": args.snr_scaled / 4.0,
        "exchanges": exchanges,
        "inbox": {
            "alice": [item.text for item in alice.inbox],
            "bob": [item.text for item in bob.inbox],
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MeshCore/bitchat bridge no-hardware simulator")
    parser.add_argument("--alice-id", default="0x000000a1", help="decimal or 0x-prefixed uint32")
    parser.add_argument("--bob-id", default="0x000000b2", help="decimal or 0x-prefixed uint32")
    parser.add_argument("--channel", type=int, default=1, help="MeshCore channel index")
    parser.add_argument("--snr-scaled", type=int, default=0, help="simulated SNR quarter-dB units")
    parser.add_argument("--alice-text", default="hello from alice over simulated MeshCore")
    parser.add_argument("--bob-text", default="ack from bob over simulated MeshCore")
    parser.add_argument("--one-way", action="store_true", help="only send alice -> bob")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.one_way:
        args.bob_text = None
    try:
        print(json.dumps(run_demo(args), indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - exercised by smoke/CLI use
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
