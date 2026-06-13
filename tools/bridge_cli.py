#!/usr/bin/env python3
"""Local CLI harness for bridge frame v0.

This intentionally does not talk to hardware. It exercises the exact frame
encoding/decoding path that will later be carried in MeshCore channel datagrams.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

try:
    from bridge_frame_codec import decode_frame, encode_frame, frames_to_text, text_to_frames
except ModuleNotFoundError:  # imported as tools.bridge_cli from tests
    from tools.bridge_frame_codec import (
        decode_frame,
        encode_frame,
        frames_to_text,
        text_to_frames,
    )


def parse_int(value: str) -> int:
    """Parse decimal or 0x-prefixed integer."""
    return int(value, 0)


def cmd_encode_text(args: argparse.Namespace) -> int:
    frames = text_to_frames(
        args.text,
        bridge_id=parse_int(args.bridge_id),
        message_id=parse_int(args.message_id),
        flags=parse_int(args.flags),
    )
    payload = {
        "type": "bridge_text_frames_v0",
        "frame_count": len(frames),
        "frames": [
            {
                "index": frame.fragment_index,
                "count": frame.fragment_count,
                "flags": f"0x{frame.flags:02x}",
                "msg_type": f"0x{frame.msg_type:02x}",
                "bridge_id": f"0x{frame.bridge_id:08x}",
                "message_id": f"0x{frame.message_id:016x}",
                "payload_len": len(frame.payload),
                "encoded_hex": encode_frame(frame).hex(),
            }
            for frame in frames
        ],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_decode_frames(args: argparse.Namespace) -> int:
    frames = [decode_frame(bytes.fromhex(frame_hex)) for frame_hex in args.frame_hex]
    text = frames_to_text(frames)
    payload = {
        "type": "bridge_text_v0",
        "frame_count": len(frames),
        "bridge_id": f"0x{frames[0].bridge_id:08x}",
        "message_id": f"0x{frames[0].message_id:016x}",
        "text": text,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MeshCore/bitchat bridge local CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    encode = sub.add_parser("encode-text", help="encode text into bridge frame hex JSON")
    encode.add_argument("--bridge-id", required=True, help="decimal or 0x-prefixed uint32")
    encode.add_argument("--message-id", required=True, help="decimal or 0x-prefixed uint64")
    encode.add_argument("--flags", default="0", help="decimal or 0x-prefixed uint8")
    encode.add_argument("text", help="UTF-8 text to encode")
    encode.set_defaults(func=cmd_encode_text)

    decode = sub.add_parser("decode-frames", help="decode bridge frame hex values into text")
    decode.add_argument("frame_hex", nargs="+", help="one or more encoded bridge frames as hex")
    decode.set_defaults(func=cmd_decode_frames)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # pragma: no cover - exercised by smoke/CLI use
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
