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
from .meshcore_companion import (
    CMD_SEND_CHANNEL_DATA,
    DATA_TYPE_DEV,
    FLOOD_PATH,
    RESP_CODE_CHANNEL_DATA_RECV,
    InboundChannelData,
    build_channel_data_command,
    parse_channel_data_recv,
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
    "frames_to_text",
    "max_text_bytes",
    "text_to_frames",
    "CMD_SEND_CHANNEL_DATA",
    "DATA_TYPE_DEV",
    "FLOOD_PATH",
    "RESP_CODE_CHANNEL_DATA_RECV",
    "InboundChannelData",
    "build_channel_data_command",
    "parse_channel_data_recv",
]
