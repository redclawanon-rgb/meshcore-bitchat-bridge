# Gate 5C — Android/iOS app insertion-point mapping

## Status

Gate 5C is a design/spike gate only. It does not modify Android or iOS code, open BLE, run mobile apps, use hardware, or claim stock bitchat interoperability.

Goal: map the `BitchatAppAdapter` contract from Gates 5A/5B onto concrete Android/iOS insertion points, then choose the least-invasive next integration path.

## Local adapter contract to satisfy

The local bridge now expects a future app/native adapter to provide two semantic directions:

```text
App/native inbound public packet or callback
  -> BitchatAppAdapter.ingest_packet_bytes(...) or equivalent semantic callback
  -> BitchatAppPublicTextEvent
  -> MeshCore bridge send path
```

```text
MeshCore delivered public text
  -> BitchatAppAdapter.publish_bridge_text(text, from_bridge_id, message_id)
  -> app/native public-message API
```

A real app integration does not have to literally expose Python bytes. It can expose an equivalent stable app-side API/event stream, but the ownership boundary should remain the same:

- app owns BLE, Noise, signatures, route planning, fragments, trust UI, lifecycle, persistence;
- MeshCore bridge owns MeshCore transport and text-event forwarding;
- adapter owns semantic translation between the two.

## Android surfaces inspected

Repo root inspected: `/tmp/bitchat-android/app/src/main/java/com/bitchat/android`

Key files and evidence:

- `ui/ChatViewModel.kt`
  - `sendMessage(content: String)` begins at line 473.
  - Public mesh send path constructs local UI message, then calls `meshService.sendMessage(content, mentions, null)` around lines 541–577.
  - Delegate callback `didReceiveMessage(message)` forwards into `MeshDelegateHandler` around lines 861–864.
- `ui/MeshDelegateHandler.kt`
  - `didReceiveMessage(message: BitchatMessage)` starts at line 27.
  - Handles app/UI dedup and dispatches public/private/channel message effects.
- `mesh/BluetoothConnectionManager.kt`
  - BLE component delegate receives decoded `BitchatPacket` at `onPacketReceived(packet, peerID, device)` around lines 45–58.
  - It ignores self packets and forwards to `delegate?.onPacketReceived(...)`.
  - Broadcast path is `broadcastPacket(routed: RoutedPacket)` around lines 281–288.
- `mesh/PacketProcessor.kt`
  - `processPacket(routed)` starts around line 73 and serializes processing per peer.
  - `handleReceivedPacket(routed)` starts around line 122.
  - Dispatches `ANNOUNCE`, `MESSAGE`, `FILE_TRANSFER`, `FRAGMENT`, `REQUEST_SYNC`, `NOISE_HANDSHAKE`, and `NOISE_ENCRYPTED` around lines 144–168.
  - `handleFragment` delegates fragment reassembly and recursively re-enters `handleReceivedPacket(...)` around lines 224–235.
- `mesh/MessageHandler.kt`
  - `handleAnnounce(...)` starts around line 217 and enforces signed verified announcements before peer registry update.
  - `handleMessage(...)` starts around line 358.
  - Broadcast message path requires a verified peer and then emits `BitchatMessage` via `delegate?.onMessageReceived(message)` around lines 383–426.
  - Message IDs for public broadcast are based on `PacketIdUtil.computeIdHex(packet)` around lines 404 and 420.
- `mesh/BluetoothMeshService.kt`
  - Wires `MessageHandlerDelegate` around lines 249+.
  - `onMessageReceived(message)` stores into `AppStateStore` and forwards to UI delegate `delegate?.didReceiveMessage(message)` around lines 389–407.
  - Signed announce send path tracks public packets for sync with `gossipSyncManager.onPublicPacketSeen(...)` around lines 1061–1077.
- `sync/GossipSyncManager.kt`
  - `onPublicPacketSeen(packet)` starts around line 96.
  - Tracks broadcast `MESSAGE` and `ANNOUNCE` only and uses `PacketIdUtil`.
- `noise/NoiseEncryptionService.kt`
  - `verifyPacketSignature(...)` around line 422 verifies Ed25519 packet signatures against public keys.

## Android recommended insertion strategy

### Android inbound app -> MeshCore bridge

Recommended initial insertion point:

```text
MessageHandler.handleBroadcastMessage(...)
  after verified-peer enforcement and UTF-8 payload decode
  before/alongside delegate?.onMessageReceived(message)
```

Why:

- It is after BLE decode, packet validation, announce trust, signature-derived peer identity, fragment reassembly, and public-message policy.
- It can emit a semantic event equivalent to `BitchatAppPublicTextEvent` without making the MeshCore bridge understand Android BLE internals.
- It naturally has: content, sender peer ID, timestamp, app message ID/packet ID, nickname, and verification context.

Alternative inbound hook:

```text
BluetoothMeshService.MessageHandlerDelegate.onMessageReceived(message)
```

This is easier because it receives app-level `BitchatMessage`, but it is lower fidelity for packet metadata (`route`, raw packet ID, original packet bytes). Use it for a UI/service bridge prototype if semantic text-only is enough.

Avoid as first insertion points:

- `BluetoothConnectionManager.onPacketReceived(...)`: too low-level; bridge would inherit BLE/device lifecycle concerns.
- `PacketProcessor.handleReceivedPacket(...)`: still too close to relay/security dispatch.
- raw `BinaryProtocol` decode paths: duplicates fixture work and bypasses app trust/policy.

### Android MeshCore bridge -> app outbound

Recommended initial insertion point:

```text
ChatViewModel.sendMessage(content)
  or a narrow service method that calls meshService.sendMessage(content, mentions, null)
```

For a background/service integration, avoid UI-only state when possible and prefer a narrow `BluetoothMeshService` method that creates/sends a public mesh message using the existing app path.

The app should still own:

- local echo/UI state;
- mention parsing if operating in UI mode;
- packet construction/signing;
- `connectionManager.broadcastPacket(...)`;
- `gossipSyncManager.onPublicPacketSeen(...)`.

### Android minimum app-side API shape

A future Android bridge module should expose a small interface conceptually like:

```kotlin
interface MeshBridgePublicTextSink {
    fun publishFromBridge(text: String, bridgeId: Int, messageId: Int)
}

interface MeshBridgePublicTextSource {
    fun onVerifiedPublicText(callback: (event: VerifiedPublicTextEvent) -> Unit)
}
```

`VerifiedPublicTextEvent` should be emitted only after app verification/policy has accepted the message.

Fields to carry:

- `text: String`
- `senderPeerID: String`
- `timestampMs: Long`
- `messageIDOrPacketID: String`
- `nickname: String?`
- optional `route: List<String>?` if available after packet processing
- `source = "android-app"`

## iOS surfaces inspected

Repo root inspected: `/tmp/bitchat-ios/bitchat`

Key files and evidence:

- `ViewModels/ChatOutgoingCoordinator.swift`
  - `sendMessage(_ content: String)` starts around line 75.
  - Public mesh messages are prepared/local-echoed and routed through `context.sendMeshMessage(...)` around lines 178–193.
- `Services/BLE/BLEService.swift`
  - Comments at lines 10–13 state BLEService emits events via `BitchatDelegate`; UI consumes `didReceivePublicMessage` and `didReceiveNoisePayload`.
  - Handler properties are split: `announceHandler`, `publicMessageHandler`, `noisePacketHandler`, `fragmentHandler`, `fileTransferHandler` around lines 119–128.
  - `sendMessage(...)` starts around line 347.
  - Public send constructs a `BitchatPacket`, signs it, marks self broadcast dedup, broadcasts, and tracks gossip around lines 366–392.
  - Packet broadcasting begins around line 855 and owns route application/fragment decisions.
- `Services/BLE/BLEPublicMessageHandler.swift`
  - `handle(_ packet: BitchatPacket, from peerID: PeerID)` starts at line 47.
  - Applies freshness/self policy, resolves verified sender display name, tracks gossip, decodes UTF-8 payload, and calls `deliverPublicMessage(...)` around lines 50–102.
- `Services/BLE/BLEFragmentHandler.swift`
  - Handles fragments, reassembles original bytes, decodes via `BinaryProtocol.decode(reassembled)`, validates, sets TTL to 0, and re-enters receive processing around lines 34–64.
- `Services/BLE/BLEAnnounceHandler.swift`
  - Handles announce preflight, signature verification, trust decision, registry/topology updates, persistence, UI events, and packet sync tracking around lines 72–180.
- `Services/BLE/BLEReceivePipeline.swift`
  - Computes receive context/dedup and relay decisions from packet/local peer state.
- `ViewModels/ChatTransportEventCoordinator.swift`
  - `didReceivePublicMessage(...)` starts around line 151.
  - Converts delegate public message callbacks into `BitchatMessage` and calls `context.handlePublicMessage(...)`.
- `ViewModels/PublicMessagePipeline.swift`
  - Batches/dedups visible public messages before committing to conversation store.
- `Sync/PacketIdUtil.swift`
  - Computes sync packet ID as SHA-256(type|sender|timestamp|payload) prefix.

## iOS recommended insertion strategy

### iOS inbound app -> MeshCore bridge

Recommended initial insertion point:

```text
BLEPublicMessageHandlerEnvironment.deliverPublicMessage(...)
  or immediately after BLEPublicMessageHandler has accepted and decoded content
```

Why:

- It is after BLE decode, freshness/self policy, verified sender resolution, fragment reassembly, and gossip tracking.
- It avoids duplicating `BinaryProtocol`, BLE queues, fragment assembly, or trust policy in the bridge.
- It can emit a semantic public-text event with peer ID, nickname, content, timestamp, and message ID.

Alternative inbound hook:

```text
ChatTransportEventCoordinator.didReceivePublicMessage(...)
```

This is easier and fully semantic, but it is closer to UI concerns. Use it for a prototype if app UI lifecycle is acceptable; prefer the BLE handler environment for a cleaner transport/service-level bridge.

Avoid as first insertion points:

- `BLEInboundWriteBuffer` / raw `BinaryProtocol.decode`: too low-level and bypasses app policy.
- `BLEReceivePipeline.context(...)`: good for metadata/dedup understanding, but not enough to deliver accepted public text alone.
- `BLEFragmentHandler` internals: fragments are already re-entered as original packets; do not bridge partial fragments.

### iOS MeshCore bridge -> app outbound

Recommended initial insertion point:

```text
BLEService.sendMessage(content, mentions: [], to: nil, messageID:, timestamp:)
```

Why:

- It already runs on `messageQueue`.
- It constructs and signs the public `BitchatPacket`.
- It marks self-broadcast dedup.
- It broadcasts via existing route/fragment/backpressure path.
- It tracks gossip sync.

If the bridge should update UI/local echo too, route through `ChatOutgoingCoordinator.sendMessage(...)` or an equivalent app-level intent. If it should act as a headless/service bridge, call a transport-level public send API that wraps `BLEService.sendMessage(...)` and keeps UI echo optional.

### iOS minimum app-side API shape

A future iOS bridge module should expose a small surface conceptually like:

```swift
struct VerifiedPublicTextEvent {
    let text: String
    let senderPeerID: PeerID
    let nickname: String
    let timestamp: Date
    let messageID: String?
    let source: String // "ios-app"
}

protocol MeshBridgePublicTextAdapter {
    func publishFromBridge(_ text: String, bridgeID: UInt8, messageID: UInt32)
    func setPublicTextHandler(_ handler: @escaping (VerifiedPublicTextEvent) -> Void)
}
```

The handler should fire only after `BLEPublicMessageHandler` acceptance.

## Cross-platform recommendation

Do not put MeshCore bridge code inside raw BLE packet handlers first. The least risky path is:

1. Define an app-side public-text adapter interface in each app.
2. Emit verified semantic public-text events after existing app acceptance policies.
3. Publish MeshCore-delivered text through existing app public-send APIs.
4. Keep app lifecycle, permissions, trust UI, Noise, BLE, route planning, fragments, sync/dedup, and persistence inside each app.
5. Keep MeshCore transport, LoRa delivery, bridge-frame fragmentation, and daemon/service runtime outside the app.

## Next gate recommendation

Gate 5D should be a local interface spec gate, not live BLE:

- write platform-neutral `APP_ADAPTER_API.md` with exact event fields and method semantics;
- add fake Android/iOS adapter contract examples or pseudo-stubs;
- update the Python `BitchatAppPublicTextEvent` fields if this mapping reveals missing metadata;
- keep live mobile modifications gated until Eric explicitly approves app repo changes.

## Explicit non-claims

Gate 5C does not prove:

- live Android integration;
- live iOS integration;
- BLE discovery/advertising;
- stock bitchat interoperability;
- mobile background execution;
- app signing/build compatibility;
- production security;
- real hardware/radio delivery.

It only maps concrete insertion points and recommends the least-invasive app-side API path.
