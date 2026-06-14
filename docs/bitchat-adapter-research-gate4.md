# Gate 4: scoped bitchat-side adapter research

Date: 2026-06-14

Purpose: decide the safest next bridge direction after the MeshCore serial daemon proved state, logging, and live reconnect recovery.

This is a research/design note only. It does not implement stock bitchat compatibility, does not open BLE, does not run mobile apps, and does not claim interoperability with existing bitchat meshes.

## Research questions

1. What current upstream bitchat code should this project pin for adapter planning?
2. Where does public text enter and exit upstream bitchat?
3. Is there a stable external API we can use from this Python/MeshCore bridge today?
4. What are the realistic adapter options, risks, and next build step?

## Upstream versions pinned

### iOS / Apple upstream

- Repository: <https://github.com/permissionlesstech/bitchat>
- Local inspection path: `/tmp/bitchat-ios`
- Commit inspected: `bbe1ed0652a5f8435accdf0ef44b028409ceab7e`
- Commit date: `2026-06-14 07:34:58 +0000`
- Commit subject: `Automated update of relay data - Sun Jun 14 07:34:58 UTC 2026`
- License file inspected: `LICENSE`
- License observed: Unlicense / public domain dedication
- Relevant current tags from remote listing: up through `v1.5.3` was observed in `git ls-remote`; this note pins `main`, not a release tag.

### Android upstream

- Repository: <https://github.com/permissionlesstech/bitchat-android>
- Local inspection path: `/tmp/bitchat-android`
- Commit inspected: `13585a9a9caf1687dec66535f78e0d918e690585`
- Commit date: `2026-06-14 07:39:17 +0000`
- Commit subject: `Automated update of relay data - Sun Jun 14 07:39:17 UTC 2026`
- License file inspected: `LICENSE.md`
- License observed: GPL-3.0
- Relevant current tags from remote listing: up through `1.7.2` was observed in `git ls-remote`; this note pins `main`, not a release tag.

## Adapter-relevant upstream facts

### iOS transport abstraction

File: `bitchat/Services/Transport.swift`

Observed facts:

- `TransportEvent` includes:
  - `publicMessageReceived(peerID:nickname:content:timestamp:messageID:)`
  - `noisePayloadReceived(...)`
  - peer lifecycle/status events
- `Transport` includes:
  - lifecycle methods: `startServices()`, `stopServices()`, `emergencyDisconnectAll()`
  - identity methods: `myPeerID`, `myNickname`, `setNickname(...)`
  - public messaging: `sendMessage(_ content: String, mentions: [String])`
  - a timestamp/messageID overload: `sendMessage(_ content: String, mentions: [String], messageID: String, timestamp: Date)`
  - private messages, delivery/read receipts, file transfer, QR verification, Noise identity/session hooks
- `BLEService` conforms to `Transport`.

Interpretation:

- iOS has a useful app-level seam, but it is an in-app Swift protocol, not an external API that the current Python daemon can call.
- A real iOS-native MeshCore transport could theoretically implement `Transport`, but that is a mobile app integration project, not a Python daemon adapter.

### iOS BLE constants and public send path

File: `bitchat/Services/BLE/BLEService.swift`

Observed constants:

- Debug service UUID: `F47B5E2D-4A9E-4C5A-9B3F-8E1D2C3A4B5A`
- Release/mainnet service UUID: `F47B5E2D-4A9E-4C5A-9B3F-8E1D2C3A4B5C`
- Characteristic UUID: `A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D`
- `messageTTL` comes from `TransportConfig.messageTTLDefault`.

Observed public send behavior around `BLEService.sendMessage(...)`:

- public text creates a `BitchatPacket` with:
  - `type: MessageType.message.rawValue`
  - `senderID: Data(hexString: myPeerID.id)`
  - `recipientID: nil`
  - `timestamp: UInt64(Date milliseconds)`
  - `payload: Data(content.utf8)`
  - `signature: nil`
  - `ttl: messageTTL`
- then upstream calls `noiseService.signPacket(basePacket)`.
- the signed packet is dedup-marked and passed to `broadcastPacket(signedPacket)`.
- gossip sync is notified with `gossipSyncManager?.onPublicPacketSeen(signedPacket)`.

Interpretation:

- Public text is UTF-8 inside packet payload, but upstream signs the packet before broadcast.
- Forging packet bytes without reproducing identity/signing/verification behavior is not enough for stock compatibility.

### iOS public receive path

File: `bitchat/Services/BLE/BLEPublicMessageHandler.swift`

Observed behavior:

- `BLEPublicMessagePolicy.evaluate(...)` gates freshness/self-echo behavior.
- sender display name must resolve from known verified peer state or `signedSenderDisplayName(packet, peerID)`.
- unknown/unverified public message senders are dropped.
- accepted packet payload is decoded as UTF-8.
- app-level delivery uses `deliverPublicMessage(peerID, nickname, content, timestamp, messageID)`.

Interpretation:

- The narrow semantic receive seam is real: accepted public packets become `(peerID, nickname, content, timestamp, messageID?)`.
- But acceptance depends on upstream peer verification/signature/registry policy, not just packet bytes.

### Android packet/protocol model

File: `app/src/main/java/com/bitchat/android/protocol/BinaryProtocol.kt`

Observed facts:

- `MessageType` values include:
  - `ANNOUNCE = 0x01`
  - `MESSAGE = 0x02`
  - `LEAVE = 0x03`
  - `NOISE_HANDSHAKE = 0x10`
  - `NOISE_ENCRYPTED = 0x11`
  - `FRAGMENT = 0x20`
  - `REQUEST_SYNC = 0x21`
  - `FILE_TRANSFER = 0x22`
- `BitchatPacket` fields include:
  - `version`
  - `type`
  - `senderID`
  - optional `recipientID`
  - `timestamp`
  - `payload`
  - optional `signature`
  - `ttl`
  - optional `route`
- Binary protocol notes in source describe:
  - v1 header size: 14 bytes
  - v2 header size: 16 bytes
  - sender ID size: 8 bytes
  - optional recipient ID: 8 bytes
  - optional signature: 64 bytes
  - flags: recipient, signature, compression, route
  - v1 payload length: 2 bytes big-endian
  - v2 payload length: 4 bytes big-endian
  - timestamp: 8 bytes big-endian
- `toBinaryDataForSigning()` explicitly excludes mutable relay TTL by encoding an unsigned copy with fixed `SYNC_TTL_HOPS`.
- `BinaryProtocol.encode(...)` may compress payloads and pads output with `MessagePadding`.
- `BinaryProtocol.decode(...)` tries raw decode first, then unpads and decodes.

Interpretation:

- Android source gives enough detail to create local packet conformance fixtures for unsigned/signed packet byte handling.
- It does not, by itself, make the Python bridge a valid bitchat peer, because identity, signing, dedup, peer verification, BLE behavior, and relay policy still matter.

### Android BLE constants and public send path

Files:

- `app/src/main/java/com/bitchat/android/util/AppConstants.kt`
- `app/src/main/java/com/bitchat/android/mesh/BluetoothMeshService.kt`

Observed constants:

- Main service UUID: `F47B5E2D-4A9E-4C5A-9B3F-8E1D2C3A4B5C`
- Characteristic UUID: `A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D`
- Descriptor UUID: `00002902-0000-1000-8000-00805f9b34fb`
- `MESSAGE_TTL_HOPS = 7`
- fragmentation constants include threshold `512`, max fragment size `469`, max fragments per ID `256`, and fragment timeout `30_000 ms`.

Observed public send behavior in `BluetoothMeshService.sendMessage(...)`:

- public text creates a `BitchatPacket` with:
  - `version = 1`
  - `type = MessageType.MESSAGE.value`
  - `senderID = hexStringToByteArray(myPeerID)`
  - `recipientID = SpecialRecipients.BROADCAST` (`8` bytes of `0xFF`)
  - `timestamp = System.currentTimeMillis()`
  - `payload = content.toByteArray(Charsets.UTF_8)`
  - `signature = null`
  - `ttl = MAX_TTL`
- then upstream calls `signPacketBeforeBroadcast(packet)`.
- then it broadcasts through `connectionManager.broadcastPacket(RoutedPacket(signedPacket))`.
- gossip sync is notified.

Interpretation:

- iOS public broadcast uses `recipientID: nil`; Android public send currently uses explicit broadcast recipient ID (`FF:FF:FF:FF:FF:FF:FF:FF`). Any stock-compatibility work must test both forms and not assume one canonical shape without conformance fixtures.

### Android public receive path

File: `app/src/main/java/com/bitchat/android/mesh/MessageHandler.kt`

Observed behavior in `handleBroadcastMessage(...)`:

- public messages from unknown or unverified peers are dropped.
- payload is first attempted as a file packet.
- fallback public text constructs `BitchatMessage` with:
  - `id = PacketIdUtil.computeIdHex(packet).uppercase()`
  - sender nickname from delegate
  - `content = String(packet.payload, Charsets.UTF_8)`
  - `senderPeerID = peerID`
  - timestamp from packet timestamp
- delivery is through `delegate?.onMessageReceived(message)`.

Interpretation:

- Android also has a semantic public text receive seam after packet/peer verification.
- It is not an external daemon API.

## Compatibility implications

### What is low-risk and true now

- This bridge already has a semantic text carrier seam that matches the post-validation public-text shape observed in upstream.
- Upstream public text payloads are UTF-8 in `MESSAGE` packets.
- Both iOS and Android expose post-acceptance public text to app/UI code as semantic messages/events.
- Current MeshCore bridge daemon can be the reliable LoRa side while bitchat integration is researched separately.

### What is not safe to claim

Do not claim any of these from the current bridge:

- stock bitchat BLE interoperability
- ability to join existing bitchat meshes
- correct bitchat packet signing/verification
- correct Noise/session behavior
- correct peer identity or nickname verification
- correct BLE fragmentation/backpressure behavior
- iOS/Android cross-version compatibility
- production privacy/security

### Why direct Python stock-BLE emulation is high risk

A Python daemon pretending to be a bitchat BLE peer would need to reproduce at least:

1. BLE central/peripheral GATT roles and CoreBluetooth/Android GATT behavior.
2. Packet binary encode/decode including padding, compression, v1/v2 length rules, routes, and fragmentation.
3. Identity material and signatures compatible with upstream verification policies.
4. Announce packets and verified nickname / signed display-name flows.
5. Peer registry/dedup/sync expectations.
6. Different iOS vs Android public broadcast recipient behavior (`nil` vs broadcast recipient ID observed at pinned commits).
7. Mobile lifecycle, scan/connect scheduling, relay fanout, and backpressure quirks.

That is not the next smallest useful step.

## Adapter options

### Option A — keep current semantic seam, add upstream conformance fixtures next

Description: keep `BitchatTextCarrier` as the local seam; add a small local `bitchat_packet_fixture`/research module and tests that encode/decode pinned upstream public `MESSAGE` packet fixtures without claiming live compatibility.

Pros:

- Lowest risk.
- Keeps no-BLE/no-stock-claim default intact.
- Produces concrete evidence before mobile/BLE work.
- Helps decide whether future packet-level bridge mode is feasible.

Cons:

- Still not live interoperability.
- Does not put messages into a stock app yet.

Recommendation: **do this next**.

### Option B — iOS-native MeshCore transport/fork

Description: build a Swift transport inside/forked from the iOS app that implements `Transport` and carries semantic public text over a MeshCore side channel.

Pros:

- Aligns with upstream iOS `Transport` abstraction.
- Avoids external packet forgery by staying inside app semantics.
- iOS repo license observed as Unlicense, lowering code-use friction.

Cons:

- Requires iOS/macOS build environment and mobile app work.
- MeshCore serial/BLE companion access from iOS must be separately designed.
- Not directly useful for the current Windows-hosted daemon.

Recommendation: viable later if Eric wants an iOS app path.

### Option C — Android-native MeshCore bridge/fork

Description: build inside/forked from Android app around `BluetoothMeshService`/`MessageHandler` semantics.

Pros:

- Android code clearly exposes public send/receive paths.
- Android may be friendlier for USB serial/OTG or foreground services.

Cons:

- Android repo is GPL-3.0; incorporating code into this MIT repo or distributing combined artifacts has copyleft implications that need intentional handling.
- Requires Android app build/sign/deploy work.
- Still outside the current Python daemon.

Recommendation: viable only if license/product direction is explicit.

### Option D — external Python stock-BLE peer emulator

Description: implement enough packet/signature/BLE behavior in Python to appear as a bitchat peer.

Pros:

- Would integrate with current daemon architecture if it worked.

Cons:

- Highest protocol/security risk.
- Easy to make a fake that sends bytes but fails verification in real apps.
- Requires live BLE hardware/app test matrix.
- Most likely path to accidental false compatibility claims.

Recommendation: **do not do this next**.

## Recommended next gate

Gate 4A: **version-pinned bitchat packet conformance fixtures, no BLE**.

Scope:

1. Pin upstream source commits from this note.
2. Add a local Python research module under `tools/bridge_frame_codec/` or `tools/research/` that can represent the subset of `BitchatPacket` needed for public text fixtures.
3. Add tests for unsigned v1 public `MESSAGE` packet encode/decode fields using deterministic values:
   - version
   - type `0x02`
   - ttl
   - timestamp
   - sender ID
   - recipient ID absent vs broadcast recipient
   - payload UTF-8 text
   - signature absent/present length handling only, not crypto validity
4. Add fixture notes that distinguish:
   - iOS observed public send shape: no recipient ID
   - Android observed public send shape: broadcast recipient ID
5. Do not implement BLE scanning/connection.
6. Do not implement signing or claim stock compatibility.
7. Run full local tests.

Exit criteria:

- Deterministic packet fixtures and tests pass.
- `BITCHAT_SEAM.md` / docs clearly state fixtures are for research and compatibility planning only.
- No live BLE, no mobile app, no production/security claim.

## Gate 4A result: packet fixture subset implemented

Gate 4A added a small local fixture module:

- `tools/bridge_frame_codec/bitchat_packet_fixture.py`

It intentionally implements only raw, unpadded v1 public-message fixture handling:

- v1 header fields:
  - `version`
  - `type`
  - `ttl`
  - `timestamp_ms`
  - `flags`
  - uint16 payload length
- fixed 8-byte sender ID
- optional 8-byte recipient ID
- UTF-8 payload bytes
- optional 64-byte signature preservation and length validation only

It explicitly does **not** implement:

- BLE scanning/connection
- padding
- compression
- fragmentation
- signing
- signature verification
- Noise sessions
- peer verification
- stock bitchat interoperability

Tests added:

- `tests/test_bitchat_packet_fixture.py`

Deterministic fixture bytes pinned by tests:

### iOS-observed public message shape: no recipient ID

Input fields:

- sender ID: `0102030405060708`
- timestamp: `0x0000018F3D2A1B00`
- ttl: `7`
- type: `0x02`
- text: `gate4a fixture`
- recipient: absent

Expected raw fixture hex:

```text
0102070000018f3d2a1b0000000e01020304050607086761746534612066697874757265
```

### Android-observed public message shape: broadcast recipient ID

Input fields:

- sender ID: `0102030405060708`
- timestamp: `0x0000018F3D2A1B00`
- ttl: `7`
- type: `0x02`
- text: `gate4a fixture`
- recipient: `ffffffffffffffff`

Expected raw fixture hex:

```text
0102070000018f3d2a1b0001000e0102030405060708ffffffffffffffff6761746534612066697874757265
```

### Signature-present length fixture

Signature-present tests preserve 64 signature bytes and reject non-64-byte signatures. This is only a structural fixture check; it is not crypto validation.

Verification result:

```text
python3 -m unittest tests.test_bitchat_packet_fixture -v
Ran 4 tests in 0.001s
OK

python3 -m unittest discover -s tests -v
Ran 69 tests in 0.339s
OK
```

Gate 4A confirms that the project now has deterministic, version-pinned packet fixture coverage for the two public-message shapes observed upstream, while preserving the no-BLE/no-stock-compatibility boundary.

## Decision from this gate

Keep the bridge's operational path as:

```text
MeshCore daemon / bridge frames
  <-> semantic public text carrier seam
  <-> future upstream-aware adapter
```

Do not jump straight from the proven MeshCore daemon into live stock-bitchat BLE emulation. The next useful technical step is packet-conformance fixture work, followed by a separately approved app-native or BLE/live interoperability gate if the fixtures prove stable.
