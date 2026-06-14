# bitchat-side Transport Seam Notes

Date inspected: 2026-06-14

MVP-16 inspected the public bitchat source to identify the smallest safe boundary for a future bridge adapter. This document is a design note only: it does not claim stock bitchat compatibility and does not implement or exercise any bitchat BLE, Noise, Nostr, mobile, or production path.

## Source inspected

Repository: `permissionlesstech/bitchat`

Public URLs inspected from GitHub `main` via GitHub API/raw content:

- Repository: <https://github.com/permissionlesstech/bitchat>
- Tree listing: <https://api.github.com/repos/permissionlesstech/bitchat/git/trees/main?recursive=1>
- `bitchat/Services/Transport.swift`: <https://raw.githubusercontent.com/permissionlesstech/bitchat/main/bitchat/Services/Transport.swift>
  - Defines an app-level `Transport` protocol with event delegates, lifecycle, peer APIs, public `sendMessage(_ content:mentions:)`, private messaging, receipts, file hooks, verification hooks, and Noise identity/session wrappers.
  - `TransportEvent.publicMessageReceived(peerID:nickname:content:timestamp:messageID:)` is the app-facing inbound public text event.
- `bitchat/Services/BLE/BLEService.swift`: <https://raw.githubusercontent.com/permissionlesstech/bitchat/main/bitchat/Services/BLE/BLEService.swift>
  - Defines BLE service/characteristic UUID constants.
  - Builds public broadcast messages as signed `BitchatPacket` values with `type = MessageType.message.rawValue`, UTF-8 payload bytes, TTL, sender ID, timestamp, and signature before `broadcastPacket(...)`.
  - Encodes packets with `toBinaryData(...)` and sends bytes through CoreBluetooth update/write paths, with fragmentation/backpressure helpers when needed.
  - Exposes lower-level `sendPacket(_ packet: BitchatPacket)` and directed packet sending for gossip sync, but those still depend on the bitchat packet/signing/BLE internals.
- `localPackages/BitFoundation/Sources/BitFoundation/BitchatPacket.swift`: <https://raw.githubusercontent.com/permissionlesstech/bitchat/main/localPackages/BitFoundation/Sources/BitFoundation/BitchatPacket.swift>
  - Defines `BitchatPacket` fields: version, type, sender ID, optional recipient ID, timestamp, payload, signature, TTL, route, RSR flag.
  - Binary encoding/decoding is delegated to `BinaryProtocol.encode/decode` via `toBinaryData(...)` and `BitchatPacket.from(...)`.
- `localPackages/BitFoundation/Sources/BitFoundation/MessageType.swift`: <https://raw.githubusercontent.com/permissionlesstech/bitchat/main/localPackages/BitFoundation/Sources/BitFoundation/MessageType.swift>
  - Defines core message types including `.message = 0x02`, `.noiseHandshake = 0x10`, `.noiseEncrypted = 0x11`, `.fragment = 0x20`, `.fileTransfer = 0x22`.
- `bitchat/Services/BLE/BLEPublicMessageHandler.swift`: <https://raw.githubusercontent.com/permissionlesstech/bitchat/main/bitchat/Services/BLE/BLEPublicMessageHandler.swift>
  - Handles inbound public message packets by validating policy/display name, decoding `packet.payload` as UTF-8, deriving a timestamp, and delivering public text to the app delegate/event layer.
- `bitchat/Services/MessageRouter.swift`: <https://raw.githubusercontent.com/permissionlesstech/bitchat/main/bitchat/Services/MessageRouter.swift>
  - Routes private/outbox messages across available app transports, reinforcing that bitchat already has an app-level transport abstraction but not a standalone minimal public-text carrier API.
- `bitchat/Services/TransportConfig.swift`: <https://raw.githubusercontent.com/permissionlesstech/bitchat/main/bitchat/Services/TransportConfig.swift>
  - Centralizes BLE/message limits and timing knobs; observed only to understand that BLE fragmentation and pacing are transport-specific concerns outside this bridge MVP.

## Safe claims

From inspection, it is safe to say:

- The public bitchat source has an app-level `Transport` protocol and `TransportEvent` model.
- Public broadcast text in the inspected BLE implementation is represented inside a `BitchatPacket` whose payload is UTF-8 text and whose type is `MessageType.message` (`0x02`).
- Inbound public BLE messages eventually cross a narrow semantic point as `(peerID, nickname, content, timestamp, messageID?)` after packet/policy/signature handling.
- Outbound public text enters the BLE path through `sendMessage(_ content:mentions:...)`, where bitchat constructs/signs/broadcasts a `BitchatPacket`.
- Packet binary compatibility, signatures, peer identity, Noise handshakes, mobile background behavior, BLE fragmentation, and Nostr routing are all owned by bitchat internals, not by this local bridge repository.

## Claims we cannot make yet

This repository must not claim:

- Stock bitchat compatibility.
- Ability to join or interoperate with existing bitchat BLE meshes.
- Correct production handling of bitchat signatures, Noise sessions, peer identity, delivery acks, Nostr, file transfer, mobile lifecycle, or BLE UUID/MTU behavior.
- Security properties beyond the current lab/local bridge-frame tests.
- That copying bitchat BLE UUIDs or packet fields is sufficient for interoperability.

The current MeshCore bridge frame is a custom tunnel for text, not a bitchat packet tunnel. Treat any future stock-compatible carrier as a separate integration effort requiring upstream-version pinning, dedicated conformance tests, and explicit scope approval.

## Narrow local adapter boundary

The local bridge should keep the bitchat side semantic and text-only for the next loop:

```text
MeshCore companion datagram transport
  -> bridge frame decode/reassembly
  -> DeliveredText(from_bridge_id, message_id, text)
  -> future BitchatTextCarrier.publish_public_text(text, source metadata)

future BitchatTextCarrier.receive_public_text(...)
  -> bridge frame text fragmentation
  -> MeshCore companion datagram transport
```

Recommended local Python seam, intentionally not named `BitchatTransport` to avoid suggesting stock compatibility:

```python
class BitchatTextCarrier(Protocol):
    def publish_public_text(self, text: str, *, from_bridge_id: int, message_id: int) -> None:
        """Accept decoded bridge text for a future bitchat-like public text carrier."""

    def recv_public_text(self) -> BitchatOutboundText | None:
        """Return one future carrier-originated public text message, if available."""
```

Supporting value object:

```python
@dataclass(frozen=True, slots=True)
class BitchatOutboundText:
    text: str
    carrier_message_id: str | None = None
```

Boundary rules:

- Input from MeshCore to this seam is decoded Unicode text plus bridge metadata only; no MeshCore packet bytes leak into the bitchat-side carrier.
- Output from this seam to MeshCore is Unicode text only; no bitchat packet bytes, BLE UUIDs, signatures, or Noise material enter bridge-frame v0.
- A first implementation should be fake/in-memory only and should verify text handoff from existing `DeliveredText` objects.
- A future real adapter may wrap an upstream bitchat app/service API if one is intentionally integrated, but this project should not forge `BitchatPacket` bytes or pretend to be a stock BLE peer in the MVP.

## Likely next local implementation loop

MVP-17 should implement the fake bitchat-side text carrier seam locally:

1. Add a small Python module such as `tools/bridge_frame_codec/bitchat_adapter.py` with `BitchatTextCarrier`, `BitchatOutboundText`, and `FakeBitchatTextCarrier`.
2. Add tests proving:
   - decoded `DeliveredText` can be handed to the fake carrier without MeshCore bytes crossing the seam;
   - fake carrier-originated text can be sent through the existing transport-neutral MeshCore path;
   - names/docs avoid stock compatibility claims.
3. Keep all tests no-hardware and no-network.
4. Continue to leave real bitchat/BLE/mobile integration as a later, explicitly scoped adapter effort.
