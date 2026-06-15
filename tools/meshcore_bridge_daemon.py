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
    from bridge_frame_codec.bridge_frame import BridgeFrameError
    from bridge_frame_codec.serial_adapter import (
        SerialCompanionDatagramTransport,
        SerialRxPacketReader,
        wrap_serial_tx_packet,
    )
    from bridge_frame_codec.sim import SimulatedBridgeNode
except ModuleNotFoundError:  # imported as tools.meshcore_bridge_daemon from tests
    from tools.bridge_frame_codec.bridge_frame import BridgeFrameError
    from tools.bridge_frame_codec.serial_adapter import (
        SerialCompanionDatagramTransport,
        SerialRxPacketReader,
        wrap_serial_tx_packet,
    )
    from tools.bridge_frame_codec.sim import SimulatedBridgeNode


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
    parser.add_argument(
        "--relay-stock-text",
        action="store_true",
        help="relay decoded stock MeshCore text messages out the other configured ports; disabled by default",
    )
    parser.add_argument(
        "--relay-stock-text-prefix",
        default="[relay] ",
        help="prefix added to relayed stock text and used as a loop guard",
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
        0x07: "contact_msg_recv",
        0x08: "channel_msg_recv",
        0x0A: "no_more_messages",
        0x10: "contact_msg_recv_v3",
        0x11: "channel_msg_recv_v3",
        0x1B: "channel_data_recv",
        0x81: "path_update",
        0x83: "msg_waiting",
        0x88: "log_rx_data",
    }.get(frame[0], f"unknown_0x{frame[0]:02x}")


def _should_poll_sync_next_after_frame(frame_type: str) -> bool:
    """Return true when a sync-next response may not have drained the queue.

    MeshCore can return queued non-channel messages before the channel-data
    datagram we care about. Keep polling after unknown sync-next responses so a
    daemon does not stop at the first unrelated queued message.
    """
    return frame_type in {
        "channel_data_recv",
        "contact_msg_recv",
        "channel_msg_recv",
        "contact_msg_recv_v3",
        "channel_msg_recv_v3",
    } or frame_type.startswith("unknown_")


def _path_len_info(plen: int) -> dict[str, int]:
    if plen == 255:
        return {"path_hash_mode": -1, "path_len": -1}
    return {"path_hash_mode": plen >> 6, "path_len": plen & 0x3F}


def _parse_meshcore_text_message(frame: bytes) -> dict[str, object] | None:
    """Parse stock MeshCore text-message sync-next responses.

    The bridge's own payload uses CHANNEL_DATA_RECV (0x1B). Stock MeshCore app
    text messages arrive from CMD_SYNC_NEXT_MESSAGE as CONTACT_MSG_RECV (0x07),
    CHANNEL_MSG_RECV (0x08), or their v3 variants (0x10/0x11). This lightweight
    parser mirrors meshcore_py's documented reader layout enough to log clean
    text events without taking ownership of the full MeshCore contact database.
    """
    if len(frame) < 2:
        return None
    packet_type = frame[0]
    try:
        if packet_type == 0x07:  # CONTACT_MSG_RECV
            if len(frame) < 13:
                return None
            plen = frame[7]
            txt_type = frame[8]
            sender_timestamp = int.from_bytes(frame[9:13], "little", signed=False)
            text_start = 17 if txt_type == 2 and len(frame) >= 17 else 13
            return {
                "message_scope": "contact",
                "pubkey_prefix": frame[1:7].hex(),
                **_path_len_info(plen),
                "txt_type": txt_type,
                "sender_timestamp": sender_timestamp,
                "text": frame[text_start:].decode("utf-8", "ignore").rstrip("\x00"),
            }
        if packet_type == 0x08:  # CHANNEL_MSG_RECV
            if len(frame) < 9:
                return None
            plen = frame[2]
            txt_type = frame[3]
            sender_timestamp = int.from_bytes(frame[4:8], "little", signed=False)
            return {
                "message_scope": "channel",
                "channel_idx": frame[1],
                **_path_len_info(plen),
                "txt_type": txt_type,
                "sender_timestamp": sender_timestamp,
                "text": frame[8:].decode("utf-8", "ignore").rstrip("\x00"),
            }
        if packet_type == 0x10:  # CONTACT_MSG_RECV_V3
            if len(frame) < 16:
                return None
            plen = frame[10]
            txt_type = frame[11]
            sender_timestamp = int.from_bytes(frame[12:16], "little", signed=False)
            text_start = 20 if txt_type == 2 and len(frame) >= 20 else 16
            return {
                "message_scope": "contact",
                "protocol_version": 3,
                "snr": int.from_bytes(frame[1:2], "little", signed=True) / 4,
                "pubkey_prefix": frame[4:10].hex(),
                **_path_len_info(plen),
                "txt_type": txt_type,
                "sender_timestamp": sender_timestamp,
                "text": frame[text_start:].decode("utf-8", "ignore").rstrip("\x00"),
            }
        if packet_type == 0x11:  # CHANNEL_MSG_RECV_V3
            if len(frame) < 12:
                return None
            plen = frame[5]
            txt_type = frame[6]
            sender_timestamp = int.from_bytes(frame[7:11], "little", signed=False)
            return {
                "message_scope": "channel",
                "protocol_version": 3,
                "snr": int.from_bytes(frame[1:2], "little", signed=True) / 4,
                "channel_idx": frame[4],
                **_path_len_info(plen),
                "txt_type": txt_type,
                "sender_timestamp": sender_timestamp,
                "text": frame[11:].decode("utf-8", "ignore").rstrip("\x00"),
            }
    except UnicodeDecodeError:
        return None
    return None


def _stock_text_dedupe_key(message: dict[str, object]) -> tuple[object, ...]:
    return (
        message.get("message_scope"),
        message.get("pubkey_prefix"),
        message.get("channel_idx"),
        message.get("sender_timestamp"),
        message.get("txt_type"),
        message.get("text"),
    )


def _build_stock_channel_text_command(text: str, channel_index: int, timestamp: int | None = None) -> bytes:
    """Build MeshCore CMD_SEND_CHANNEL_TXT_MSG for stock text relay."""
    if not 0 <= channel_index <= 255:
        raise ValueError("channel index must fit in one byte")
    if timestamp is None:
        timestamp = int(time.time())
    return b"\x03\x00" + channel_index.to_bytes(1, "little") + int(timestamp).to_bytes(4, "little") + text.encode("utf-8")


def _should_relay_stock_text(message: dict[str, object], relay_prefix: str) -> tuple[bool, str]:
    text = message.get("text")
    if not isinstance(text, str) or not text:
        return False, "empty"
    if message.get("message_scope") != "contact":
        return False, "non_contact"
    if relay_prefix and relay_prefix in text:
        return False, "loop_guard"
    return True, "ok"


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
        "relay_stock_text": bool(args.relay_stock_text),
        "relay_stock_text_prefix": args.relay_stock_text_prefix,
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
    relay_sent_count = 0
    relay_skipped_count = 0
    relayed_stock_text_keys: set[tuple[object, ...]] = set()

    try:
        record("daemon_plan", ports=ports, injections=injections, state_loaded=bool(state))
        if not args.open_real_ports:
            result["event_count"] = len(events)
            result["delivered_count"] = 0
            result["parse_error_count"] = 0
            result["reconnect_count"] = 0
            result["relay_sent_count"] = 0
            result["relay_skipped_count"] = 0
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
                    meshcore_text = _parse_meshcore_text_message(frame)
                    if meshcore_text is not None:
                        frame_event["meshcore_text"] = meshcore_text
                        record(
                            "meshcore_text_message",
                            name=name,
                            device=ports[name],
                            frame_type=frame_type,
                            **meshcore_text,
                        )
                        if args.relay_stock_text:
                            text = meshcore_text.get("text")
                            should_relay, skip_reason = _should_relay_stock_text(meshcore_text, args.relay_stock_text_prefix)
                            if not should_relay:
                                relay_skipped_count += 1
                                record(
                                    f"relay_stock_text_skipped_{skip_reason}",
                                    name=name,
                                    device=ports[name],
                                    frame_type=frame_type,
                                    text=text if isinstance(text, str) else None,
                                )
                            else:
                                dedupe_key = _stock_text_dedupe_key(meshcore_text)
                                if dedupe_key in relayed_stock_text_keys:
                                    relay_skipped_count += 1
                                    record(
                                        "relay_stock_text_skipped_duplicate",
                                        name=name,
                                        device=ports[name],
                                        frame_type=frame_type,
                                        dedupe_key=[str(part) for part in dedupe_key],
                                        text=text,
                                    )
                                else:
                                    relayed_stock_text_keys.add(dedupe_key)
                                    relay_text = args.relay_stock_text_prefix + text
                                    command = _build_stock_channel_text_command(relay_text, args.channel)
                                    target_count = 0
                                    for relay_name, relay_ser in serials.items():
                                        if relay_name == name or relay_ser is None:
                                            continue
                                        try:
                                            relay_ser.write(wrap_serial_tx_packet(command))  # type: ignore[attr-defined]
                                            target_count += 1
                                            relay_sent_count += 1
                                            record(
                                                "relay_stock_text_sent",
                                                source=name,
                                                target=relay_name,
                                                source_device=ports[name],
                                                target_device=ports[relay_name],
                                                channel_index=args.channel,
                                                text=relay_text,
                                                command_hex=command.hex(),
                                            )
                                        except Exception as exc:
                                            relay_skipped_count += 1
                                            record(
                                                "relay_stock_text_error",
                                                source=name,
                                                target=relay_name,
                                                source_device=ports[name],
                                                target_device=ports[relay_name],
                                                error={"type": type(exc).__name__, "message": str(exc)},
                                            )
                                            close_port(relay_name, "relay_stock_text_error")
                                    if target_count == 0:
                                        relay_skipped_count += 1
                                        record("relay_stock_text_skipped_no_targets", name=name, device=ports[name], text=text)
                    if _should_poll_sync_next_after_frame(frame_type):
                        try:
                            ser.write(wrap_serial_tx_packet(b"\x0a"))  # type: ignore[attr-defined]
                            frame_event["polled_sync_next_message_after_frame"] = True
                        except Exception as exc:
                            frame_event["poll_error_after_frame"] = {"type": type(exc).__name__, "message": str(exc)}
                            close_port(name, "poll_error_after_frame")
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
    result["relay_sent_count"] = relay_sent_count
    result["relay_skipped_count"] = relay_skipped_count
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
