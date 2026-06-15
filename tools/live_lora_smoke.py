#!/usr/bin/env python3
"""Gated live two-port MeshCore serial/LoRa smoke.

This utility opens two MeshCore USB Companion serial ports, sends bridge text from
one port, and listens for MeshCore CHANNEL_DATA_RECV notifications on the other.
It is intentionally separate from no-hardware smoke CLIs: live serial access
requires --open-real-ports.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from typing import Sequence

try:
    from bridge_frame_codec import SimulatedBridgeNode
    from bridge_frame_codec.bridge_frame import BridgeFrameError
    from bridge_frame_codec.serial_adapter import (
        SerialCompanionDatagramTransport,
        SerialRxPacketReader,
        wrap_serial_tx_packet,
    )
except ModuleNotFoundError:  # imported as tools.live_lora_smoke from tests
    from tools.bridge_frame_codec import SimulatedBridgeNode
    from tools.bridge_frame_codec.bridge_frame import BridgeFrameError
    from tools.bridge_frame_codec.serial_adapter import (
        SerialCompanionDatagramTransport,
        SerialRxPacketReader,
        wrap_serial_tx_packet,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Live two-port MeshCore LoRa smoke")
    parser.add_argument("--tx-port", required=True, help="sender MeshCore USB Companion port")
    parser.add_argument("--rx-port", required=True, help="receiver MeshCore USB Companion port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--channel", type=int, default=1)
    parser.add_argument("--tx-bridge-id", default="0x000000a1")
    parser.add_argument("--rx-bridge-id", default="0x000000b2")
    parser.add_argument("--listen-seconds", type=float, default=20.0)
    parser.add_argument("--settle-seconds", type=float, default=0.5)
    parser.add_argument(
        "--open-real-ports",
        action="store_true",
        help="required to open serial ports and transmit; without it, only reports planned parameters",
    )
    parser.add_argument("text", help="UTF-8 text to encode/send")
    return parser


def _json_safe_error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def _classify_frame(frame: bytes) -> str:
    if not frame:
        return "empty"
    return {
        0x00: "ok",
        0x01: "error",
        0x0A: "no_more_messages",
        0x1B: "channel_data_recv",
        0x83: "msg_waiting",
        0x88: "log_rx_data",
    }.get(frame[0], f"unknown_0x{frame[0]:02x}")


def _should_poll_sync_next_after_frame(frame_type: str) -> bool:
    return frame_type == "channel_data_recv" or frame_type.startswith("unknown_")


def run(args: argparse.Namespace) -> dict[str, object]:
    tx_node = SimulatedBridgeNode(
        bridge_id=int(args.tx_bridge_id, 0),
        channel_index=args.channel,
    )
    rx_node = SimulatedBridgeNode(
        bridge_id=int(args.rx_bridge_id, 0),
        channel_index=args.channel,
    )
    commands = tx_node.make_text_commands(args.text)

    result: dict[str, object] = {
        "type": "meshcore_bitchat_bridge_live_lora_smoke_v0",
        "mode": "real-ports-opened" if args.open_real_ports else "dry-run-no-ports-opened",
        "tx_port": args.tx_port,
        "rx_port": args.rx_port,
        "baud": args.baud,
        "channel_index": args.channel,
        "tx_bridge_id": int(args.tx_bridge_id, 0),
        "rx_bridge_id": int(args.rx_bridge_id, 0),
        "listen_seconds": args.listen_seconds,
        "text_bytes": len(args.text.encode("utf-8")),
        "command_count": len(commands),
        "command_hex": [command.hex() for command in commands],
        "notifications": [],
        "delivered": [],
        "parse_errors": [],
        "raw_rx_hex_chunks": [],
    }
    if not args.open_real_ports:
        return result

    try:
        import serial  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - env dependent
        raise RuntimeError("pyserial is required for --open-real-ports") from exc

    rx_reader = SerialRxPacketReader()
    deadline = time.monotonic() + args.listen_seconds
    with serial.Serial(args.rx_port, args.baud, timeout=0.1) as rx_serial:
        time.sleep(args.settle_seconds)
        tx_transport = SerialCompanionDatagramTransport(
            port=args.tx_port,
            baud=args.baud,
            open_real_port=True,
        )
        for command in commands:
            tx_transport.send_channel_data_command(command)

        while time.monotonic() < deadline:
            chunk = rx_serial.read(1024)
            if chunk:
                result["raw_rx_hex_chunks"].append(chunk.hex())  # type: ignore[index, union-attr]
                for notification in rx_reader.feed(chunk):
                    frame_type = _classify_frame(notification)
                    item: dict[str, object] = {
                        "hex": notification.hex(),
                        "len": len(notification),
                        "frame_type": frame_type,
                    }
                    if frame_type == "msg_waiting":
                        # MeshCore queues received messages/datagrams and emits
                        # 0x83; host must poll CMD_SYNC_NEXT_MESSAGE (0x0A).
                        rx_serial.write(wrap_serial_tx_packet(b"\x0a"))
                        item["polled_sync_next_message"] = True
                    if notification and notification[0] == 0x1B:
                        try:
                            delivered = rx_node.receive_notification(notification)
                            if delivered is not None:
                                result["delivered"].append(asdict(delivered))  # type: ignore[index, union-attr]
                                item["delivered"] = asdict(delivered)
                        except BridgeFrameError as exc:
                            result["parse_errors"].append(  # type: ignore[index, union-attr]
                                {"notification_hex": notification.hex(), "error": _json_safe_error(exc)}
                            )
                    if _should_poll_sync_next_after_frame(frame_type):
                        rx_serial.write(wrap_serial_tx_packet(b"\x0a"))
                        item["polled_sync_next_message_after_frame"] = True
                    result["notifications"].append(item)  # type: ignore[index, union-attr]
            if result["delivered"]:  # type: ignore[index]
                break

    result["delivered_count"] = len(result["delivered"])  # type: ignore[arg-type]
    result["notification_count"] = len(result["notifications"])  # type: ignore[arg-type]
    result["raw_rx_chunk_count"] = len(result["raw_rx_hex_chunks"])  # type: ignore[arg-type]
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args), indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - exercised by live CLI use
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
