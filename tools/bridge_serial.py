#!/usr/bin/env python3
"""Dry-run serial bytes for the MeshCore/bitchat bridge.

This does not open a serial port. It prints the exact packet bytes that a future
serial adapter would write for a text message.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

try:
    from bridge_frame_codec import SimulatedBridgeNode
    from bridge_frame_codec.serial_adapter import wrap_serial_tx_packet
except ModuleNotFoundError:  # imported as tools.bridge_serial from tests
    from tools.bridge_frame_codec import SimulatedBridgeNode
    from tools.bridge_frame_codec.serial_adapter import wrap_serial_tx_packet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MeshCore bridge serial dry-run")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="shown only; not opened")
    parser.add_argument("--baud", type=int, default=115200, help="shown only; not opened")
    parser.add_argument("--bridge-id", default="0x000000a1", help="decimal or 0x-prefixed uint32")
    parser.add_argument("--channel", type=int, default=1, help="MeshCore channel index")
    parser.add_argument("text", help="UTF-8 text to encode for serial dry-run")
    return parser


def run(args: argparse.Namespace) -> dict[str, object]:
    node = SimulatedBridgeNode(bridge_id=int(args.bridge_id, 0), channel_index=args.channel)
    commands = node.make_text_commands(args.text)
    packets = [wrap_serial_tx_packet(command) for command in commands]
    return {
        "type": "meshcore_bitchat_bridge_serial_dry_run_v0",
        "mode": "dry-run-no-port-opened",
        "port": args.port,
        "baud": args.baud,
        "channel_index": args.channel,
        "text_bytes": len(args.text.encode("utf-8")),
        "packet_count": len(packets),
        "packets": [
            {
                "index": index,
                "serial_tx_hex": packet.hex(),
                "companion_command_hex": commands[index].hex(),
                "serial_len": len(packet),
                "companion_command_len": len(commands[index]),
            }
            for index, packet in enumerate(packets)
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args), indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - exercised by smoke/CLI use
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
