# Gate 5H — Android debug hook mapping / patch plan

## Status

Created: 2026-06-15 08:45 EDT

Gate 5H is a no-live-BLE mapping/patch-plan gate. It does **not** modify Android app code beyond the already completed Gate 5G disabled adapter stub, does not wire BLE or message paths, does not run a mobile app/device/emulator, does not touch MeshCore hardware, and does not claim stock bitchat interoperability.

## Inputs

- Android checkout: `/tmp/bitchat-android`
- Android branch with disabled adapter: `gate5g-android-adapter-stub`
- Android adapter commit: `5592c3f Add disabled Mesh bridge Android adapter stub`
- Bridge API spec: `docs/APP_ADAPTER_API.md`
- Prior insertion map: `docs/bitchat-app-insertion-points-gate5c.md`
- Gate 5G evidence: `docs/android-app-adapter-stub-gate5g.md`

## Current Android surfaces re-inspected

### Inbound public text: `MessageHandler.handleBroadcastMessage(...)`

File:

```text
/tmp/bitchat-android/app/src/main/java/com/bitchat/android/mesh/MessageHandler.kt
```

Relevant lines:

```text
383 private suspend fun handleBroadcastMessage(routed: RoutedPacket)
387-392 drops public messages from unverified/unknown peers
418-426 plain text fallback builds BitchatMessage and calls delegate?.onMessageReceived(message)
```

Important current behavior:

- `handleMessage(routed)` ignores self peer IDs before routing to broadcast/private handling.
- `handleBroadcastMessage(...)` enforces verified peer policy before public text creation.
- File transfer payloads are handled separately and should not be bridged as text.
- Plain public text is decoded with `String(packet.payload, Charsets.UTF_8)` and gets:
  - `id = PacketIdUtil.computeIdHex(packet).uppercase()`
  - `sender = delegate?.getPeerNickname(peerID) ?: "unknown"`
  - `content = ...`
  - `senderPeerID = peerID`
  - `timestamp = Date(packet.timestamp.toLong())`

Best future inbound hook location:

```text
MessageHandler.handleBroadcastMessage(...)
  after verified peer check
  after plain text BitchatMessage construction
  before or alongside delegate?.onMessageReceived(message)
```

Why this is still the best hook:

- It is after BLE decode, packet validation, sender verification, and public-message policy.
- It skips file/private/control messages.
- It has packet ID, peer ID, nickname, timestamp, and accepted text.

### Inbound alternative: `BluetoothMeshService.onMessageReceived(...)`

File:

```text
/tmp/bitchat-android/app/src/main/java/com/bitchat/android/mesh/BluetoothMeshService.kt
```

Relevant lines:

```text
389 override fun onMessageReceived(message: BitchatMessage)
390-404 stores messages in AppStateStore
405-406 forwards to UI delegate
```

Pros:

- Easier to hook at a service-level semantic message boundary.
- Already receives a `BitchatMessage` after app handling.

Cons:

- It is less precise: public/private/channel/file filtering must be rechecked here.
- It may be closer to app store/UI behavior than transport acceptance policy.
- It may lack original packet metadata beyond `message.id`.

Use this only if the first implementation wants the smallest no-risk debug event tap and accepts lower metadata fidelity.

### Outbound bridge text: `BluetoothMeshService.sendMessage(...)`

File:

```text
/tmp/bitchat-android/app/src/main/java/com/bitchat/android/mesh/BluetoothMeshService.kt
```

Relevant lines:

```text
703 fun sendMessage(content: String, mentions: List<String> = emptyList(), channel: String? = null)
704 ignores empty content
706 serviceScope.launch
707-716 constructs broadcast MESSAGE BitchatPacket
718-720 signs and broadcasts packet
721-722 tracks own broadcast for sync
```

Best future outbound hook location:

```text
A narrow debug wrapper method on BluetoothMeshService
  debugPublishBridgePublicText(text, bridgeId, messageId)
    -> validates adapter/config is enabled
    -> calls sendMessage(text, emptyList(), null)
    -> returns accepted-for-send, not delivery proof
```

Why:

- It preserves app ownership of packet construction, signing, route/fragment/backpressure behavior, and gossip tracking.
- It does not require the MeshCore bridge to write raw BLE packets.
- It creates a clean seam for tests before runtime enabling.

## Recommended Gate 5I code shape

If Eric continues after this plan, the next code gate should be **Gate 5I Android disabled hook wrappers**, not live runtime/device testing.

### 1. Add an adapter owner to `BluetoothMeshService`

Add a private adapter instance defaulting disabled:

```kotlin
private val meshBridgeAdapter = DebugMeshBridgePublicTextAdapter()
```

Or, preferably for tests, allow package-private/debug-only injection through a tiny method:

```kotlin
internal fun setDebugMeshBridgeAdapterForTesting(adapter: MeshBridgePublicTextAdapter?)
```

Do not read config from network, files, UI, or remote settings yet.

### 2. Add service-level outbound wrapper only

```kotlin
fun debugPublishBridgePublicText(
    text: String,
    bridgeId: Int,
    messageId: Long,
): MeshBridgePublishResult
```

Default result should be `adapter_disabled` and send nothing.

When explicitly enabled in tests, the wrapper may delegate to the adapter's injected debug publisher. A later gate can connect that debug publisher to `sendMessage(...)` only after tests prove behavior.

### 3. Add inbound event mapper function without wiring it live first

Add a pure mapper function in the bridge package, not in BLE code:

```kotlin
fun mapAcceptedPublicMessageToBridgeEvent(
    message: BitchatMessage,
    packetIdHex: String,
): MeshBridgeVerifiedPublicTextEvent?
```

It should return null for:

- blank content;
- private messages;
- channel messages if the first bridge mode is contact/public timeline only;
- file/media messages;
- missing sender peer ID;
- missing/blank packet/message ID.

Then tests can prove mapping before live hook wiring.

### 4. Only after the pure mapper exists, consider one disabled live tap

Future patch point:

```kotlin
// after plain text BitchatMessage construction in handleBroadcastMessage(...)
meshBridgeAdapter.emitVerifiedPublicText(mappedEvent)
```

But the default disabled adapter must make this a no-op.

## Tests required before any live wiring

Gate 5I/5J tests should cover:

1. default disabled wrapper sends nothing;
2. outbound wrapper rejects blank/overlong/bad IDs before app send path;
3. mapper emits event for accepted public text;
4. mapper rejects private/channel/file/blank/missing peer cases;
5. enabled debug-only path can call an injected fake publisher without BLE;
6. no test requires Android device/emulator/BLE permissions.

## Stop criteria

Stop before code or live execution if any step would require:

- real Android device/emulator runtime;
- BLE scan/advertise/connect permissions;
- app signing or APK release;
- upstream fork/PR/push;
- changing the running MeshCore Windows daemon;
- claiming stock bitchat compatibility or production security.

## Recommended next gate

**Gate 5I — Android pure mapper + disabled service wrapper tests.**

This is still safe, local, and compile-testable. It should not connect live BLE or send messages through `BluetoothMeshService.sendMessage(...)` yet; it should create testable seams that make the eventual live hook small and reversible.
