#!/usr/bin/env python3
"""Gated continuous MeshCore USB Companion bridge daemon skeleton.

This is the MeshCore-side daemon spine for the bridge. It can open one or more
MeshCore USB Companion serial ports, poll queued datagrams, decode bridge text,
and optionally inject test text on a selected port. It does not implement the
real bitchat side yet.

Real serial access requires --open-real-ports. Without that flag the command is
a dry-run plan and opens no ports.
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
except ModuleNotFoundError:  # imported as tools.meshcore_bridge_daemon from tests
    from tools.bridge_frame_codec import SimulatedBridgeNode
    from tools.bridge_frame_codec.bridge_frame import BridgeFrameError
    from tools.bridge_frame_codec.serial_adapter import (
        SerialCompanionDatagramTransport,
        SerialRxPacketReader,
        wrap_serial_tx_packet,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MeshCore bridge daemon skeleton")
    parser.add_argument(
        "--port",
        action="append",
        default=[],
        metavar="NAME=DEVICE",
        help="MeshCore serial port mapping, e.g. pocket1=COM5. Repeatable.",
    )
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--channel", type=int, default=1)
    parser.add_argument("--bridge-id-base", default="0x000000a1")
    parser.add_argument(
        "--message-id-start",
        type=int,
        default=None,
        help="initial bridge message id; defaults to a time-derived value to avoid daemon restart collisions",
    )
    parser.add_argument("--duration-seconds", type=float, default=10.0)
    parser.add_argument("--poll-interval-seconds", type=float, default=0.05)
    parser.add_argument(
        "--inject-text",
        action="append",
        default=[],
        metavar="NAME:TEXT",
        help="Optional test injection sent through the named port after opening. Repeatable.",
    )
    parser.add_argument(
        "--open-real-ports",
        action="store_true",
        help="required to open serial ports; default is dry-run/no-open",
    )
    return parser


def _parse_ports(items: list[str]) -> dict[str, str]:
    ports: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"invalid --port {item!r}; expected NAME=DEVICE")
        name, device = item.split("=", 1)
        name = name.strip()
        device = device.strip()
        if not name or not device:
            raise ValueError(f"invalid --port {item!r}; expected NAME=DEVICE")
        if name in ports:
            raise ValueError(f"duplicate port name: {name}")
        ports[name] = device
    if not ports:
        raise ValueError("at least one --port NAME=DEVICE is required")
    return ports


def _parse_injections(items: list[str], ports: dict[str, str]) -> list[tuple[str, str]]:
    injections: list[tuple[str, str]] = []
    for item in items:
        if ":" not in item:
            raise ValueError(f"invalid --inject-text {item!r}; expected NAME:TEXT")
        name, text = item.split(":", 1)
        name = name.strip()
        if name not in ports:
            raise ValueError(f"inject target {name!r} is not a configured --port name")
        if not text:
            raise ValueError("injected text must not be empty")
        injections.append((name, text))
    return injections


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


def _event(kind: str, **fields: object) -> dict[str, object]:
    return {"kind": kind, "ts_monotonic": time.monotonic(), **fields}


def run(args: argparse.Namespace) -> dict[str, object]:
    ports = _parse_ports(args.port)
    injections = _parse_injections(args.inject_text, ports)
    bridge_id_base = int(args.bridge_id_base, 0)
    message_id_start = args.message_id_start
    if message_id_start is None:
        message_id_start = int(time.time()) & 0xFFFF
    result: dict[str, object] = {
        "type": "meshcore_bitchat_bridge_daemon_v0",
        "mode": "real-ports-opened" if args.open_real_ports else "dry-run-no-ports-opened",
        "ports": ports,
        "baud": args.baud,
        "channel_index": args.channel,
        "bridge_id_base": bridge_id_base,
        "message_id_start": message_id_start,
        "duration_seconds": args.duration_seconds,
        "injection_count": len(injections),
        "events": [],
    }
    events: list[dict[str, object]] = result["events"]  # type: ignore[assignment]
    events.append(_event("daemon_plan", ports=ports, injections=injections))
    if not args.open_real_ports:
        result["event_count"] = len(events)
        result["delivered_count"] = 0
        result["parse_error_count"] = 0
        return result

    try:
        import serial  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - env dependent
        raise RuntimeError("pyserial is required for --open-real-ports") from exc

    serials = {}
    readers = {name: SerialRxPacketReader() for name in ports}
    nodes = {
        name: SimulatedBridgeNode(
            bridge_id=bridge_id_base + index,
            channel_index=args.channel,
            _next_message_id=message_id_start,
        )
        for index, name in enumerate(ports)
    }
    delivered_count = 0
    parse_error_count = 0
    try:
        for name, device in ports.items():
            serials[name] = serial.Serial(device, args.baud, timeout=0)
            events.append(_event("port_opened", name=name, device=device))

        for name, text in injections:
            commands = nodes[name].make_text_commands(text)
            for command in commands:
                serials[name].write(wrap_serial_tx_packet(command))
            events.append(
                _event(
                    "injected_text",
                    name=name,
                    device=ports[name],
                    text=text,
                    command_count=len(commands),
                )
            )

        deadline = time.monotonic() + args.duration_seconds
        while time.monotonic() < deadline:
            saw_data = False
            for name, ser in serials.items():
                chunk = ser.read(1024)
                if not chunk:
                    continue
                saw_data = True
                events.append(_event("serial_chunk", name=name, hex=chunk.hex(), length=len(chunk)))
                for frame in readers[name].feed(chunk):
                    frame_type = _classify_frame(frame)
                    frame_event = _event(
                        "companion_frame",
                        name=name,
                        frame_type=frame_type,
                        hex=frame.hex(),
                        length=len(frame),
                    )
                    if frame_type == "msg_waiting":
                        ser.write(wrap_serial_tx_packet(b"\x0a"))
                        frame_event["polled_sync_next_message"] = True
                    if frame_type == "channel_data_recv":
                        try:
                            delivered = nodes[name].receive_notification(frame)
                            if delivered is not None:
                                delivered_count += 1
                                frame_event["delivered"] = asdict(delivered)
                        except BridgeFrameError as exc:
                            parse_error_count += 1
                            frame_event["parse_error"] = {"type": type(exc).__name__, "message": str(exc)}
                        # Continue polling after a queued message; MeshCore may
                        # have more than one message queued even if it only sent
                        # one msg_waiting push.
                        ser.write(wrap_serial_tx_packet(b"\x0a"))
                        frame_event["polled_sync_next_message_after_channel_data"] = True
                    events.append(frame_event)
            if not saw_data:
                time.sleep(args.poll_interval_seconds)
    finally:
        for name, ser in serials.items():
            try:
                ser.close()
                events.append(_event("port_closed", name=name, device=ports[name]))
            except Exception as exc:  # pragma: no cover - cleanup best-effort
                events.append(_event("port_close_error", name=name, error=str(exc)))

    result["event_count"] = len(events)
    result["delivered_count"] = delivered_count
    result["parse_error_count"] = parse_error_count
    return result


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
