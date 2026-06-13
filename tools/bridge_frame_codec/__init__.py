"""Bridge frame v0 codec for MeshCore ↔ bitchat bridge MVP."""

from .bridge_frame import (
    BridgeFrame,
    BridgeFrameError,
    MAGIC,
    VERSION,
    MAX_CARRIER_PAYLOAD,
    FIXED_OVERHEAD,
    MAX_FRAME_PAYLOAD,
    crc16_xmodem,
    encode_frame,
    decode_frame,
    fragment_payload,
    reassemble_fragments,
)
from .message import frames_to_text, max_text_bytes, text_to_frames

__all__ = [
    "BridgeFrame",
    "BridgeFrameError",
    "MAGIC",
    "VERSION",
    "MAX_CARRIER_PAYLOAD",
    "FIXED_OVERHEAD",
    "MAX_FRAME_PAYLOAD",
    "crc16_xmodem",
    "encode_frame",
    "decode_frame",
    "fragment_payload",
    "reassemble_fragments",
    "frames_to_text",
    "max_text_bytes",
    "text_to_frames",
]
