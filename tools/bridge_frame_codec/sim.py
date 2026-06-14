"""No-hardware two-node simulator for the MeshCore bridge MVP.

The simulator exercises the local stack without BLE, serial, or radios:

text -> bridge frames -> MeshCore companion channel-data command bytes ->
RESP_CODE_CHANNEL_DATA_RECV notification bytes -> bridge decode/reassembly -> text
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .bridge_frame import BridgeFrame, BridgeFrameError, decode_frame, encode_frame
from .message import frames_to_text, text_to_frames
from .meshcore_companion import (
    CMD_SEND_CHANNEL_DATA,
    DATA_TYPE_DEV,
    FLOOD_PATH,
    RESP_CODE_CHANNEL_DATA_RECV,
    build_channel_data_command,
    parse_channel_data_recv,
)


@dataclass(frozen=True, slots=True)
class DeliveredText:
    """A text message delivered by the simulator."""

    from_bridge_id: int
    message_id: int
    text: str


@dataclass(slots=True)
class SimulatedBridgeNode:
    """A bridge endpoint with local MeshCore companion framing behavior."""

    bridge_id: int
    channel_index: int = 1
    data_type: int = DATA_TYPE_DEV
    _next_message_id: int = 1
    _fragments: dict[tuple[int, int, int], dict[int, BridgeFrame]] = field(
        default_factory=dict
    )
    _delivered_keys: set[tuple[int, int, int]] = field(default_factory=set)
    inbox: list[DeliveredText] = field(default_factory=list)

    def make_text_commands(self, text: str) -> list[bytes]:
        """Encode text as outbound MeshCore companion channel-data commands."""
        message_id = self._next_message_id
        self._next_message_id += 1
        frames = text_to_frames(text, bridge_id=self.bridge_id, message_id=message_id)
        return [
            build_channel_data_command(
                encode_frame(frame),
                channel_index=self.channel_index,
                data_type=self.data_type,
            )
            for frame in frames
        ]

    def receive_notification(self, raw: bytes) -> DeliveredText | None:
        """Receive one simulated MeshCore channel-data notification.

        Returns a DeliveredText when a full message becomes available, otherwise
        None. Exact duplicate fragments and already-delivered duplicate messages
        are ignored safely. Corrupt frames or conflicting duplicate fragments
        raise BridgeFrameError.
        """
        inbound = parse_channel_data_recv(raw)
        if inbound.data_type != self.data_type:
            return None
        frame = decode_frame(inbound.payload)
        key = (frame.bridge_id, frame.message_id, frame.msg_type)
        if key in self._delivered_keys:
            return None

        bucket = self._fragments.setdefault(key, {})
        existing = bucket.get(frame.fragment_index)
        if existing is not None:
            if existing.payload != frame.payload:
                raise BridgeFrameError("conflicting duplicate fragment")
            return None

        bucket[frame.fragment_index] = frame
        if len(bucket) != frame.fragment_count:
            return None

        ordered = [bucket[index] for index in range(frame.fragment_count)]
        text = frames_to_text(ordered)
        delivered = DeliveredText(
            from_bridge_id=frame.bridge_id,
            message_id=frame.message_id,
            text=text,
        )
        self.inbox.append(delivered)
        self._delivered_keys.add(key)
        del self._fragments[key]
        return delivered


class SimulatedMeshCoreLink:
    """A deterministic in-memory link between simulated bridge nodes."""

    def __init__(self, *, snr_scaled: int = 0):
        self.snr_scaled = snr_scaled

    def command_to_notification(self, command: bytes) -> bytes:
        """Convert an outbound channel-data command into an inbound notification."""
        if len(command) < 5:
            raise BridgeFrameError(f"channel-data command too short: {len(command)} < 5")
        if command[0] != CMD_SEND_CHANNEL_DATA:
            raise BridgeFrameError(f"unexpected command: 0x{command[0]:02x}")
        channel_index = command[1]
        path_len = command[2]
        if path_len == FLOOD_PATH:
            data_type_offset = 3
        else:
            data_type_offset = 3 + path_len
        if len(command) < data_type_offset + 2:
            raise BridgeFrameError("channel-data command missing data_type")
        data_type = int.from_bytes(command[data_type_offset : data_type_offset + 2], "little")
        payload = command[data_type_offset + 2 :]
        if len(payload) > 0xFF:
            raise BridgeFrameError("notification payload too large for one-byte length")
        return (
            bytes([RESP_CODE_CHANNEL_DATA_RECV])
            + int(self.snr_scaled).to_bytes(1, "little", signed=True)
            + b"\x00\x00"
            + bytes([channel_index, path_len])
            + data_type.to_bytes(2, "little")
            + bytes([len(payload)])
            + payload
        )

    def deliver(self, sender: SimulatedBridgeNode, receiver: SimulatedBridgeNode, text: str) -> list[DeliveredText]:
        """Send text from one simulated node to another."""
        delivered: list[DeliveredText] = []
        for command in sender.make_text_commands(text):
            maybe = receiver.receive_notification(self.command_to_notification(command))
            if maybe is not None:
                delivered.append(maybe)
        return delivered
