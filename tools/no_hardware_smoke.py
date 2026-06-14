#!/usr/bin/env python3
"""Run documented no-hardware demo CLIs and emit a stable JSON transcript.

This script intentionally uses only local subprocess calls to the documented demo
CLIs. It does not pass any flags that open serial/BLE/hardware/network paths;
``bridge_serial.py`` is invoked in its default dry-run mode.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]


class SmokeError(RuntimeError):
    """Raised when a no-hardware smoke subprocess fails or prints invalid JSON."""


def _run_json(command: list[str]) -> dict[str, Any]:
    """Run a documented CLI command and return its JSON object output."""
    run_command = [sys.executable, *command[1:]]
    completed = subprocess.run(
        run_command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SmokeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stderr: {completed.stderr.strip()}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive path
        raise SmokeError(f"invalid JSON from {' '.join(command)}: {exc}") from exc
    if not isinstance(payload, dict):  # pragma: no cover - defensive path
        raise SmokeError(f"expected JSON object from {' '.join(command)}")
    return payload


def _sim_summary(payload: dict[str, Any]) -> dict[str, Any]:
    exchanges = payload["exchanges"]
    first = exchanges[0]
    delivered = first["delivered"][0]
    return {
        "type": payload["type"],
        "mode": payload["mode"],
        "exchange_count": len(exchanges),
        "first_exchange": {
            "from": first["from"],
            "to": first["to"],
            "command_count": first["command_count"],
            "notification_count": first["notification_count"],
            "delivered_count": first["delivered_count"],
            "delivered_text": delivered["text"],
        },
        "inbox": {
            "alice_count": len(payload["inbox"]["alice"]),
            "bob_count": len(payload["inbox"]["bob"]),
            "bob_texts": payload["inbox"]["bob"],
        },
    }


def _serial_summary(payload: dict[str, Any]) -> dict[str, Any]:
    first_packet = payload["packets"][0]
    return {
        "type": payload["type"],
        "mode": payload["mode"],
        "port": payload["port"],
        "baud": payload["baud"],
        "packet_count": payload["packet_count"],
        "first_packet": {
            "index": first_packet["index"],
            "serial_len": first_packet["serial_len"],
            "companion_command_len": first_packet["companion_command_len"],
            "serial_tx_hex_prefix": first_packet["serial_tx_hex"][:2],
            "companion_command_hex_prefix": first_packet["companion_command_hex"][:2],
        },
    }


def _pump_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": payload["type"],
        "mode": payload["mode"],
        "safety": payload["safety"],
        "seeded": payload["seeded"],
        "pump_counts": payload["pump_counts"],
        "carrier": {
            "published_count": payload["carrier"]["published_count"],
            "published_texts": [
                item["text"] for item in payload["carrier"]["published_messages"]
            ],
            "queued_public_texts_remaining": payload["carrier"][
                "queued_public_texts_remaining"
            ],
        },
        "receiver": {
            "delivered_count": payload["receiver"]["delivered_count"],
            "inbox_texts": payload["receiver"]["inbox_texts"],
        },
        "transport": payload["transport"],
    }


def build_transcript() -> dict[str, Any]:
    """Run all documented no-hardware demo CLIs and summarize stable fields."""
    demos = [
        {
            "name": "bridge_sim_one_way",
            "command": [
                "python3",
                "tools/bridge_sim.py",
                "--one-way",
                "--alice-text",
                "smoke test over simulated MeshCore",
            ],
            "summary_fn": _sim_summary,
        },
        {
            "name": "bridge_serial_dry_run",
            "command": [
                "python3",
                "tools/bridge_serial.py",
                "--port",
                "/dev/ttyUSB0",
                "serial smoke",
            ],
            "summary_fn": _serial_summary,
        },
        {
            "name": "bridge_pump_demo",
            "command": ["python3", "tools/bridge_pump_demo.py"],
            "summary_fn": _pump_summary,
        },
    ]

    transcript_demos = []
    for demo in demos:
        payload = _run_json(demo["command"])
        transcript_demos.append(
            {
                "name": demo["name"],
                "command": demo["command"],
                "stable_fields": demo["summary_fn"](payload),
            }
        )

    return {
        "type": "meshcore_bitchat_bridge_no_hardware_smoke_v0",
        "mode": "no-hardware",
        "safety": {
            "opens_ble": False,
            "opens_serial": False,
            "opens_network": False,
            "uses_real_hardware": False,
            "stock_bitchat_compatibility": "not-claimed",
        },
        "demo_count": len(transcript_demos),
        "demos": transcript_demos,
    }


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        print("usage: no_hardware_smoke.py", file=sys.stderr)
        return 2
    try:
        print(json.dumps(build_transcript(), indent=2, sort_keys=True))
        return 0
    except SmokeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
