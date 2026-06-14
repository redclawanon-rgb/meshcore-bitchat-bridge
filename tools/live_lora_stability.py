#!/usr/bin/env python3
"""Gated bidirectional MeshCore LoRa stability runner.

Runs repeated one-message live_lora_smoke attempts between two MeshCore USB
Companion serial ports. Real hardware access requires --open-real-ports.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from typing import Sequence

try:
    import live_lora_smoke
except ModuleNotFoundError:  # imported as tools.live_lora_stability from tests
    from tools import live_lora_smoke


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Live two-port MeshCore LoRa stability loop")
    parser.add_argument("--port-a", required=True, help="first MeshCore USB Companion port")
    parser.add_argument("--port-b", required=True, help="second MeshCore USB Companion port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--channel", type=int, default=1)
    parser.add_argument("--count", type=int, default=20, help="total messages to send, alternating directions")
    parser.add_argument("--listen-seconds", type=float, default=10.0)
    parser.add_argument("--settle-seconds", type=float, default=0.2)
    parser.add_argument("--pause-seconds", type=float, default=0.2)
    parser.add_argument("--label", default="gate2e", help="text prefix for unique test messages")
    parser.add_argument(
        "--open-real-ports",
        action="store_true",
        help="required to open serial ports and transmit; without it, only reports planned attempts",
    )
    return parser


def _attempt_args(args: argparse.Namespace, index: int, tx_port: str, rx_port: str, text: str) -> argparse.Namespace:
    return live_lora_smoke.build_parser().parse_args(
        [
            "--tx-port",
            tx_port,
            "--rx-port",
            rx_port,
            "--baud",
            str(args.baud),
            "--channel",
            str(args.channel),
            "--listen-seconds",
            str(args.listen_seconds),
            "--settle-seconds",
            str(args.settle_seconds),
            *( ["--open-real-ports"] if args.open_real_ports else [] ),
            text,
        ]
    )


def _latency_stats(latencies: list[float]) -> dict[str, float | None]:
    if not latencies:
        return {"min": None, "avg": None, "max": None, "median": None}
    return {
        "min": min(latencies),
        "avg": statistics.mean(latencies),
        "max": max(latencies),
        "median": statistics.median(latencies),
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    if args.count < 1:
        raise ValueError("--count must be >= 1")

    attempts: list[dict[str, object]] = []
    delivered = 0
    failed = 0
    parse_error_count = 0
    notification_type_counts: dict[str, int] = {}
    delivered_texts: set[str] = set()
    duplicate_deliveries = 0

    for i in range(args.count):
        if i % 2 == 0:
            tx_port, rx_port, direction = args.port_a, args.port_b, "A_to_B"
        else:
            tx_port, rx_port, direction = args.port_b, args.port_a, "B_to_A"
        text = f"{args.label} #{i + 1:03d} {direction}"
        start = time.monotonic()
        smoke = live_lora_smoke.run(_attempt_args(args, i, tx_port, rx_port, text))
        latency = time.monotonic() - start
        raw_notifications = smoke.get("notifications", [])
        notifications = raw_notifications if isinstance(raw_notifications, list) else []
        frame_types: list[str] = []
        for item in notifications:
            if isinstance(item, dict):
                frame_type = item.get("frame_type")
                if isinstance(frame_type, str):
                    frame_types.append(frame_type)
                    notification_type_counts[frame_type] = notification_type_counts.get(frame_type, 0) + 1

        raw_delivered_items = smoke.get("delivered", [])
        delivered_items = raw_delivered_items if isinstance(raw_delivered_items, list) else []
        is_delivered = bool(delivered_items)
        if is_delivered:
            delivered += 1
            for item in delivered_items:
                if isinstance(item, dict):
                    delivered_text = item.get("text")
                    if isinstance(delivered_text, str):
                        if delivered_text in delivered_texts:
                            duplicate_deliveries += 1
                        delivered_texts.add(delivered_text)
        else:
            failed += 1
        raw_parse_errors = smoke.get("parse_errors", [])
        parse_errors = raw_parse_errors if isinstance(raw_parse_errors, list) else []
        parse_error_count += len(parse_errors)
        attempts.append(
            {
                "index": i + 1,
                "direction": direction,
                "tx_port": tx_port,
                "rx_port": rx_port,
                "text": text,
                "latency_seconds": latency,
                "delivered": is_delivered,
                "delivered_count": smoke.get("delivered_count", 0),
                "notification_count": smoke.get("notification_count", 0),
                "frame_types": frame_types,
                "parse_error_count": len(parse_errors) if isinstance(parse_errors, list) else None,
            }
        )
        if args.pause_seconds:
            time.sleep(args.pause_seconds)

    latencies: list[float] = []
    for item in attempts:
        latency_value = item.get("latency_seconds")
        if item["delivered"] and isinstance(latency_value, float):
            latencies.append(latency_value)
    return {
        "type": "meshcore_bitchat_bridge_live_lora_stability_v0",
        "mode": "real-ports-opened" if args.open_real_ports else "dry-run-no-ports-opened",
        "port_a": args.port_a,
        "port_b": args.port_b,
        "baud": args.baud,
        "channel_index": args.channel,
        "count": args.count,
        "delivered": delivered,
        "failed": failed,
        "delivery_rate": delivered / args.count,
        "duplicate_deliveries": duplicate_deliveries,
        "parse_error_count": parse_error_count,
        "notification_type_counts": notification_type_counts,
        "latency_seconds": _latency_stats(latencies),
        "attempts": attempts,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args), indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - live CLI error path
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
