"""Message-level helpers for bridge frame v0."""

from __future__ import annotations

from .bridge_frame import (
    BridgeFrame,
    BridgeFrameError,
    MAX_FRAME_PAYLOAD,
    MSG_TEXT_FRAGMENT,
    fragment_payload,
    reassemble_fragments,
)


def text_to_frames(
    text: str,
    *,
    bridge_id: int,
    message_id: int,
    flags: int = 0,
) -> list[BridgeFrame]:
    """Encode UTF-8 text into TEXT_FRAGMENT frames.

    Splitting happens on bytes, not characters. Reassembly decodes UTF-8 only
    after all fragments are joined, so multi-byte codepoints may span fragments.
    """
    payload = text.encode("utf-8")
    return fragment_payload(
        payload,
        flags=flags,
        msg_type=MSG_TEXT_FRAGMENT,
        bridge_id=bridge_id,
        message_id=message_id,
    )


def frames_to_text(frames: list[BridgeFrame]) -> str:
    """Reassemble TEXT_FRAGMENT frames and decode UTF-8 text."""
    for frame in frames:
        if frame.msg_type != MSG_TEXT_FRAGMENT:
            raise BridgeFrameError(f"unexpected msg_type for text: 0x{frame.msg_type:02x}")
    payload = reassemble_fragments(frames)
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BridgeFrameError("invalid UTF-8 text payload") from exc


def max_text_bytes() -> int:
    """Maximum text bytes representable in one bridge message v0."""
    return MAX_FRAME_PAYLOAD * 255
