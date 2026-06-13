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
]
