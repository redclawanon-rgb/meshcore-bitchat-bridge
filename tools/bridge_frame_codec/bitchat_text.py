"""Semantic bitchat-side public text carrier seam for local bridge tests.

This module is intentionally text-only. It does not model BLE, stock bitchat
packet bytes, Noise sessions, signatures, peer identity, or production
interoperability. Future live adapters can implement this seam around an
intentionally integrated app/service API; the fake carrier here only supports
local no-hardware tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class BitchatPublishedText:
    """Decoded bridge text published into a bitchat-like public text carrier."""

    text: str
    from_bridge_id: int
    message_id: int


@dataclass(frozen=True, slots=True)
class BitchatOutboundText:
    """Public text originated by a bitchat-like carrier for MeshCore forwarding."""

    text: str
    carrier_message_id: str | None = None


class BitchatTextCarrier(Protocol):
    """Minimal semantic public-text seam for the bridge's bitchat side."""

    def publish_public_text(
        self,
        text: str,
        *,
        from_bridge_id: int,
        message_id: int,
    ) -> None:
        """Accept decoded bridge text plus bridge metadata."""

    def recv_public_text(self) -> BitchatOutboundText | None:
        """Return one carrier-originated public text item, if available."""


@dataclass(slots=True)
class FakeBitchatTextCarrier:
    """In-memory semantic text carrier for no-hardware bridge tests.

    ``published_texts`` records text that arrived from MeshCore after bridge
    frame decoding/reassembly. ``queue_public_text`` seeds carrier-originated
    public text that can then be consumed by existing MeshCore transport-neutral
    helpers. No packet bytes cross this seam in either direction.
    """

    published_texts: list[BitchatPublishedText] = field(default_factory=list)
    queued_public_texts: list[BitchatOutboundText] = field(default_factory=list)

    def publish_public_text(
        self,
        text: str,
        *,
        from_bridge_id: int,
        message_id: int,
    ) -> None:
        self.published_texts.append(
            BitchatPublishedText(
                text=text,
                from_bridge_id=from_bridge_id,
                message_id=message_id,
            )
        )

    def queue_public_text(
        self,
        text: str,
        *,
        carrier_message_id: str | None = None,
    ) -> None:
        """Queue one fake carrier-originated public text item."""
        self.queued_public_texts.append(
            BitchatOutboundText(text=text, carrier_message_id=carrier_message_id)
        )

    def recv_public_text(self) -> BitchatOutboundText | None:
        if not self.queued_public_texts:
            return None
        return self.queued_public_texts.pop(0)
