"""MeshCore companion channel-data frame helpers.

These helpers build/parse local bytes for the already-documented MeshCore
companion datagram path. They do not perform BLE/serial I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bridge_frame import BridgeFrameError, MAX_CARRIER_PAYLOAD

CMD_SEND_CHANNEL_DATA = 0x3E
RESP_CODE_CHANNEL_DATA_RECV = 0x1B
DATA_TYPE_DEV = 0xFFFF
FLOOD_PATH = 0xFF
MAX_CHANNEL_INDEX = 7


@dataclass(frozen=True, slots=True)
class InboundChannelData:
    snr_scaled: int
    channel_index: int
    path_len: int
    data_type: int
    payload: bytes

    @property
    def snr_db(self) -> float:
        return self.snr_scaled / 4.0


def _validate_channel_index(channel_index: int) -> None:
    if not 0 <= channel_index <= MAX_CHANNEL_INDEX:
        raise BridgeFrameError(f"channel_index out of range: {channel_index}")


def _validate_data_type(data_type: int) -> None:
    if not 0 <= data_type <= 0xFFFF:
        raise BridgeFrameError(f"data_type out of range: {data_type}")
    if data_type == 0:
        raise BridgeFrameError("data_type 0x0000 is reserved/invalid")


def build_channel_data_command(
    bridge_payload: bytes,
    *,
    channel_index: int,
    data_type: int = DATA_TYPE_DEV,
    path: bytes | None = None,
) -> bytes:
    """Build companion command `0x3E` for channel data datagram send.

    If `path` is None, the command uses `path_len = 0xFF` for flood routing.
    Otherwise the path bytes are included and `path_len` is their byte length.
    """
    _validate_channel_index(channel_index)
    _validate_data_type(data_type)
    if len(bridge_payload) > MAX_CARRIER_PAYLOAD:
        raise BridgeFrameError(
            f"bridge payload too large for MeshCore channel data: "
            f"{len(bridge_payload)} > {MAX_CARRIER_PAYLOAD}"
        )
    if path is None:
        path_len = FLOOD_PATH
        path_bytes = b""
    else:
        if len(path) > 0xFE:
            raise BridgeFrameError("path too long")
        path_len = len(path)
        path_bytes = path
    return (
        bytes([CMD_SEND_CHANNEL_DATA, channel_index, path_len])
        + path_bytes
        + data_type.to_bytes(2, "little")
        + bridge_payload
    )


def parse_channel_data_recv(raw: bytes) -> InboundChannelData:
    """Parse `RESP_CODE_CHANNEL_DATA_RECV` (`0x1B`) notification bytes."""
    if len(raw) < 9:
        raise BridgeFrameError(f"inbound channel data frame too short: {len(raw)} < 9")
    if raw[0] != RESP_CODE_CHANNEL_DATA_RECV:
        raise BridgeFrameError(f"unexpected response code: 0x{raw[0]:02x}")
    snr_scaled = int.from_bytes(raw[1:2], "little", signed=True)
    channel_index = raw[4]
    _validate_channel_index(channel_index)
    path_len = raw[5]
    data_type = int.from_bytes(raw[6:8], "little")
    _validate_data_type(data_type)
    data_len = raw[8]
    expected_len = 9 + data_len
    if len(raw) != expected_len:
        raise BridgeFrameError(f"inbound length mismatch: got {len(raw)}, expected {expected_len}")
    if data_len > MAX_CARRIER_PAYLOAD:
        raise BridgeFrameError(
            f"inbound payload too large: {data_len} > {MAX_CARRIER_PAYLOAD}"
        )
    return InboundChannelData(
        snr_scaled=snr_scaled,
        channel_index=channel_index,
        path_len=path_len,
        data_type=data_type,
        payload=raw[9:],
    )
