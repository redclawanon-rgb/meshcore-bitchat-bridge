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
from pathlib import Path
from typing import TextIO, Sequence

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
    parser.add_argument("--reconnect-interval-seconds", type=float, default=1.0)
    parser.add_argument(
        "--event-log",
        default=None,
        help="optional JSONL event log path; parent directories are created",
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="optional persistent JSON state path for next message IDs",
    )
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


def _open_event_log(path: str | None) -> TextIO | None:
    if path is None:
        return None
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved.open("a", encoding="utf-8")


def _record_event(events: list[dict[str, object]], log: TextIO | None, event: dict[str, object]) -> None:
    events.append(event)
    if log is not None:
        log.write(json.dumps(event, sort_keys=True) + "\n")
        log.flush()


def _load_state(path: str | None) -> dict[str, object]:
    if path is None:
        return {}
    resolved = Path(path)
    if not resolved.exists():
        return {}
    with resolved.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("state file must contain a JSON object")
    return loaded


def _state_message_id_start(state: dict[str, object], fallback: int) -> int:
    value = state.get("next_message_id")
    if isinstance(value, int) and value > 0:
        return value
    return fallback


def _save_state(path: str | None, nodes: dict[str, SimulatedBridgeNode]) -> None:
    if path is None:
        return
    next_message_id = max((node._next_message_id for node in nodes.values()), default=1)
    payload = {
        "type": "meshcore_bitchat_bridge_daemon_state_v0",
        "updated_unix": time.time(),
        "next_message_id": next_message_id,
        "ports": {name: {"bridge_id": node.bridge_id, "next_message_id": node._next_message_id} for name, node in nodes.items()},
    }
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    tmp = resolved.with_suffix(resolved.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    tmp.replace(resolved)


def run(args: argparse.Namespace) -> dict[str, object]:
    ports = _parse_ports(args.port)
    injections = _parse_injections(args.inject_text, ports)
    bridge_id_base = int(args.bridge_id_base, 0)
    state = _load_state(args.state_file)
    fallback_message_id_start = args.message_id_start
    if fallback_message_id_start is None:
        fallback_message_id_start = int(time.time()) & 0xFFFF
    message_id_start = _state_message_id_start(state, fallback_message_id_start)
    result: dict[str, object] = {
        "type": "meshcore_bitchat_bridge_daemon_v0",
        "mode": "real-ports-opened" if args.open_real_ports else "dry-run-no-ports-opened",
        "ports": ports,
        "baud": args.baud,
        "channel_index": args.channel,
        "bridge_id_base": bridge_id_base,
        "message_id_start": message_id_start,
        "duration_seconds": args.duration_seconds,
        "event_log": args.event_log,
        "state_file": args.state_file,
        "injection_count": len(injections),
        "events": [],
    }
    events: list[dict[str, object]] = result["events"]  # type: ignore[assignment]
    event_log = _open_event_log(args.event_log)

    def record(kind: str, **fields: object) -> None:
        _record_event(events, event_log, _event(kind, **fields))

    serials: dict[str, object | None] = {}
    nodes: dict[str, SimulatedBridgeNode] = {}
    delivered_count = 0
    parse_error_count = 0
    reconnect_count = 0

    try:
        record("daemon_plan", ports=ports, injections=injections, state_loaded=bool(state))
        if not args.open_real_ports:
            result["event_count"] = len(events)
            result["delivered_count"] = 0
            result["parse_error_count"] = 0
            result["reconnect_count"] = 0
            return result

        try:
            import serial  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:  # pragma: no cover - env dependent
            raise RuntimeError("pyserial is required for --open-real-ports") from exc

        readers = {name: SerialRxPacketReader() for name in ports}
        nodes = {
            name: SimulatedBridgeNode(
                bridge_id=bridge_id_base + index,
                channel_index=args.channel,
                _next_message_id=message_id_start,
            )
            for index, name in enumerate(ports)
        }
        next_reconnect_at = {name: 0.0 for name in ports}

        def close_port(name: str, reason: str) -> None:
            ser = serials.get(name)
            if ser is None:
                return
            try:
                ser.close()  # type: ignore[attr-defined]
                record("port_closed", name=name, device=ports[name], reason=reason)
            except Exception as exc:  # pragma: no cover - cleanup best-effort
                record("port_close_error", name=name, device=ports[name], reason=reason, error=str(exc))
            serials[name] = None

        def open_due_ports(now: float) -> None:
            nonlocal reconnect_count
            for name, device in ports.items():
                if serials.get(name) is not None or now < next_reconnect_at[name]:
                    continue
                try:
                    serials[name] = serial.Serial(device, args.baud, timeout=0)
                    readers[name] = SerialRxPacketReader()
                    record("port_opened", name=name, device=device)
                except Exception as exc:
                    serials[name] = None
                    reconnect_count += 1
                    next_reconnect_at[name] = now + args.reconnect_interval_seconds
                    record(
                        "port_open_failed",
                        name=name,
                        device=device,
                        error={"type": type(exc).__name__, "message": str(exc)},
                        next_retry_seconds=args.reconnect_interval_seconds,
                    )

        open_due_ports(time.monotonic())

        for name, text in injections:
            ser = serials.get(name)
            if ser is None:
                record("inject_skipped_port_closed", name=name, device=ports[name], text=text)
                continue
            commands = nodes[name].make_text_commands(text)
            try:
                for command in commands:
                    ser.write(wrap_serial_tx_packet(command))  # type: ignore[attr-defined]
                record(
                    "injected_text",
                    name=name,
                    device=ports[name],
                    text=text,
                    command_count=len(commands),
                )
            except Exception as exc:
                record("inject_error", name=name, device=ports[name], error={"type": type(exc).__name__, "message": str(exc)})
                close_port(name, "inject_error")

        deadline = time.monotonic() + args.duration_seconds
        while time.monotonic() < deadline:
            now = time.monotonic()
            open_due_ports(now)
            saw_data = False
            for name in list(ports):
                ser = serials.get(name)
                if ser is None:
                    continue
                try:
                    chunk = ser.read(1024)  # type: ignore[attr-defined]
                except Exception as exc:
                    record("serial_read_error", name=name, device=ports[name], error={"type": type(exc).__name__, "message": str(exc)})
                    close_port(name, "read_error")
                    next_reconnect_at[name] = time.monotonic() + args.reconnect_interval_seconds
                    continue
                if not chunk:
                    continue
                saw_data = True
                record("serial_chunk", name=name, hex=chunk.hex(), length=len(chunk))
                for frame in readers[name].feed(chunk):
                    frame_type = _classify_frame(frame)
                    frame_event: dict[str, object] = {
                        "name": name,
                        "frame_type": frame_type,
                        "hex": frame.hex(),
                        "length": len(frame),
                    }
                    if frame_type == "msg_waiting":
                        try:
                            ser.write(wrap_serial_tx_packet(b"\x0a"))  # type: ignore[attr-defined]
                            frame_event["polled_sync_next_message"] = True
                        except Exception as exc:
                            frame_event["poll_error"] = {"type": type(exc).__name__, "message": str(exc)}
                            close_port(name, "poll_error")
                    if frame_type == "channel_data_recv":
                        try:
                            delivered = nodes[name].receive_notification(frame)
                            if delivered is not None:
                                delivered_count += 1
                                frame_event["delivered"] = asdict(delivered)
                        except BridgeFrameError as exc:
                            parse_error_count += 1
                            frame_event["parse_error"] = {"type": type(exc).__name__, "message": str(exc)}
                        try:
                            ser.write(wrap_serial_tx_packet(b"\x0a"))  # type: ignore[attr-defined]
                            frame_event["polled_sync_next_message_after_channel_data"] = True
                        except Exception as exc:
                            frame_event["poll_error_after_channel_data"] = {"type": type(exc).__name__, "message": str(exc)}
                            close_port(name, "poll_error_after_channel_data")
                    record("companion_frame", **frame_event)
            if not saw_data:
                time.sleep(args.poll_interval_seconds)
    finally:
        for name in list(serials):
            ser = serials.get(name)
            if ser is not None:
                try:
                    ser.close()  # type: ignore[attr-defined]
                    _record_event(events, event_log, _event("port_closed", name=name, device=ports[name], reason="daemon_stop"))
                except Exception as exc:  # pragma: no cover - cleanup best-effort
                    _record_event(events, event_log, _event("port_close_error", name=name, device=ports[name], reason="daemon_stop", error=str(exc)))
        if nodes:
            _save_state(args.state_file, nodes)
            if args.state_file is not None:
                _record_event(events, event_log, _event("state_saved", path=args.state_file))
        if event_log is not None:
            event_log.close()

    result["event_count"] = len(events)
    result["delivered_count"] = delivered_count
    result["parse_error_count"] = parse_error_count
    result["reconnect_count"] = reconnect_count
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
