# Gate 5D — Platform-neutral app adapter API

## Status

Gate 5D is a local API-spec gate. It does not modify Android or iOS app repositories, open BLE, open serial ports, run mobile apps, use hardware, or claim stock bitchat interoperability.

This document turns the Gate 5A/5B Python seam and the Gate 5C Android/iOS insertion-point mapping into a platform-neutral contract that future Android and iOS adapters can implement.

## Ownership boundary

The contract intentionally stays semantic. The MeshCore bridge must not own app internals.

App/native side owns:

- BLE/CoreBluetooth/Android Bluetooth lifecycle;
- BLE stream assembly and fragmentation;
- Noise sessions and encrypted/private payloads;
- Ed25519 signing and verification;
- verified peer registry and trust UI;
- public-message freshness/self/dedup policy;
- route planning, relays, and gossip sync tracking;
- local echo, UI, persistence, notifications, and background execution.

MeshCore bridge side owns:

- MeshCore companion transport;
- bridge-frame encode/decode and fragmentation;
- LoRa text delivery and daemon/runtime behavior;
- forwarding accepted app public-text events to MeshCore;
- publishing MeshCore-delivered public text into the app adapter.

Adapter side owns:

- translating app-accepted public text into a stable event shape;
- translating bridge-delivered text into the app's existing public-send API;
- preserving dedup/source metadata;
- reporting failures without leaking app internals into the bridge core.

## Direction A: app/native public text -> MeshCore bridge

### Event name

```text
VerifiedPublicTextEvent
```

### Emission rule

Emit this event only after the app has accepted the public message according to its own existing policy.

The event must be downstream of:

- packet decode;
- fragment reassembly;
- freshness/staleness checks;
- self-echo policy;
- sender/announce/signature verification or existing accepted app policy;
- public text payload decode;
- app-level dedup policy where the app already applies one.

The event must not be emitted for:

- private DMs;
- Noise handshake/encrypted control payloads;
- announcements;
- file/image/audio transfer payloads;
- partial fragments;
- unverified/unknown public messages the app would normally drop;
- messages rejected by blocklists/trust policy;
- malformed or non-UTF-8 public text.

### Required fields

```text
text: string
sender_peer_id: string
timestamp_ms: integer
packet_id_hex: string
platform: enum("android", "ios", "fixture")
accepted: boolean
```

Semantics:

- `text`: UTF-8 public message content after app payload decoding. Do not include transport wrappers.
- `sender_peer_id`: app peer identity string, usually hex. Use the identity the app accepted as the sender.
- `timestamp_ms`: message timestamp in Unix epoch milliseconds, preserving the app packet timestamp where available.
- `packet_id_hex`: stable app-side message/packet ID used for dedup/diagnostics. Prefer the app's existing gossip/sync packet ID if available.
- `platform`: source platform of the event.
- `accepted`: must be `true` for emitted events. It exists to make the acceptance boundary explicit in logs/tests; rejected messages should not be emitted.

### Optional fields

```text
nickname: string | null
app_message_id: string | null
route: list<string> | null
source: string | null
```

Semantics:

- `nickname`: display name resolved by the app after its sender/trust rules.
- `app_message_id`: app UI/model message ID if distinct from `packet_id_hex`.
- `route`: app route hop peer IDs if available after app receive processing; omit if not exposed.
- `source`: adapter implementation source label for local diagnostics, e.g. `fixture`, `android-app`, `ios-app`.

### Dedup expectations

- The app may already drop duplicates before emitting.
- The adapter should also avoid forwarding the same `packet_id_hex` twice to MeshCore during one runtime session.
- The MeshCore bridge may still perform its own bridge-frame/message dedup later; this contract does not require app adapters to understand MeshCore internals.

### Error behavior

Rejected or malformed app messages should not throw into the bridge core as normal control flow. They should be recorded through app/native logs if the app would normally log them.

Adapter errors should be reserved for adapter boundary failures, such as:

- unable to serialize a valid accepted event;
- callback delivery failure;
- bridge sink unavailable;
- conflicting duplicate fragment or impossible metadata in fixture/local tests.

## Direction B: MeshCore bridge -> app/native public text

### Method name

```text
publishBridgePublicText
```

### Required input fields

```text
text: string
from_bridge_id: integer
message_id: integer
timestamp_ms: integer | null
```

Semantics:

- `text`: public text delivered over MeshCore and decoded from bridge frames.
- `from_bridge_id`: MeshCore bridge-node ID that originated the bridge message.
- `message_id`: bridge-local message ID for dedup/diagnostics.
- `timestamp_ms`: MeshCore/bridge delivery timestamp if available; if absent, the app may use its current send timestamp.

### Optional input fields

```text
nickname: string | null
metadata: map<string, string> | null
```

Semantics:

- `nickname`: optional display/source label for UI-level integrations. A transport-level send may ignore it.
- `metadata`: optional non-secret diagnostics such as `source=meshcore` or lab run IDs. Do not pass secrets, tokens, raw keys, or private payloads.

### Send rule

A bridge-delivered public text should enter the app through the app's existing public-message send path, not raw packet write paths.

The app should own:

- local echo decision;
- mentions/channel handling if applicable;
- packet construction;
- signing;
- self-broadcast dedup marking;
- BLE route/fragment/backpressure send;
- gossip sync tracking.

### Local echo mode

Adapters should choose one explicit local echo mode:

```text
none
app-default
bridge-origin-system-message
```

- `none`: send over app transport without adding a visible local message.
- `app-default`: let normal app send behavior create local echo.
- `bridge-origin-system-message`: visible as a bridge/system-originated public message, if the app supports that distinction.

Gate 5D recommends `app-default` for UI-driven prototypes and `none` for headless/service adapters unless Eric chooses otherwise.

### Return value

The platform-neutral result shape is:

```text
PublishBridgePublicTextResult
  accepted_for_send: boolean
  app_message_id: string | null
  packet_id_hex: string | null
  error_code: string | null
  error_message: string | null
```

`accepted_for_send=true` means the app accepted the text into its send pipeline. It does not prove BLE/radio delivery.

Recommended error codes:

```text
app_not_ready
message_too_long
send_rejected
permission_unavailable
transport_unavailable
unsupported_channel
internal_error
```

## Android pseudo-interface

```kotlin
data class VerifiedPublicTextEvent(
    val text: String,
    val senderPeerID: String,
    val timestampMs: Long,
    val packetIdHex: String,
    val platform: String = "android",
    val accepted: Boolean = true,
    val nickname: String? = null,
    val appMessageID: String? = null,
    val route: List<String>? = null,
    val source: String = "android-app"
)

data class PublishBridgePublicTextResult(
    val acceptedForSend: Boolean,
    val appMessageID: String? = null,
    val packetIdHex: String? = null,
    val errorCode: String? = null,
    val errorMessage: String? = null
)

interface MeshBridgePublicTextAdapter {
    fun setVerifiedPublicTextHandler(handler: (VerifiedPublicTextEvent) -> Unit)

    fun publishBridgePublicText(
        text: String,
        fromBridgeID: Int,
        messageID: Int,
        timestampMs: Long? = null,
        nickname: String? = null,
        metadata: Map<String, String> = emptyMap()
    ): PublishBridgePublicTextResult
}
```

Recommended Android first hook from Gate 5C:

```text
inbound: MessageHandler.handleBroadcastMessage(...), after verified-peer enforcement and UTF-8 decode
outbound: narrow wrapper around meshService.sendMessage(content, mentions, null)
```

## iOS pseudo-interface

```swift
struct VerifiedPublicTextEvent {
    let text: String
    let senderPeerID: String
    let timestampMs: Int64
    let packetIDHex: String
    let platform: String // "ios"
    let accepted: Bool // true for emitted events
    let nickname: String?
    let appMessageID: String?
    let route: [String]?
    let source: String // "ios-app"
}

struct PublishBridgePublicTextResult {
    let acceptedForSend: Bool
    let appMessageID: String?
    let packetIDHex: String?
    let errorCode: String?
    let errorMessage: String?
}

protocol MeshBridgePublicTextAdapter {
    func setVerifiedPublicTextHandler(_ handler: @escaping (VerifiedPublicTextEvent) -> Void)

    func publishBridgePublicText(
        text: String,
        fromBridgeID: UInt8,
        messageID: UInt32,
        timestampMs: Int64?,
        nickname: String?,
        metadata: [String: String]
    ) -> PublishBridgePublicTextResult
}
```

Recommended iOS first hook from Gate 5C:

```text
inbound: BLEPublicMessageHandlerEnvironment.deliverPublicMessage(...)
outbound: BLEService.sendMessage(content, mentions: [], to: nil, messageID:, timestamp:)
```

## Python fixture alignment

The local Python fixture event is `BitchatAppPublicTextEvent` in:

```text
tools/bridge_frame_codec/bitchat_app_adapter.py
```

Gate 5D aligns it with the platform-neutral contract using backward-compatible optional fields:

```text
text
packet_id_hex
sender_id
timestamp_ms
route
nickname
app_message_id
platform
accepted
source
```

The local fixture remains intentionally limited:

- `platform = "fixture"`
- `source = "fixture"`
- `accepted = True`
- `nickname = None`
- `app_message_id = None`

## Non-goals and non-claims

Gate 5D does not prove:

- Android app build or runtime integration;
- iOS app build or runtime integration;
- BLE discovery/advertising;
- mobile background behavior;
- stock bitchat interoperability;
- Noise/private-message support;
- file/image/audio support;
- production security;
- radio delivery.

It only specifies the semantic adapter API that later live app work should implement.

## Next gate recommendation

Gate 5E should choose one implementation direction:

1. Android-first app adapter stub behind a disabled/debug flag;
2. iOS-first app adapter stub behind a disabled/debug flag;
3. bridge daemon/service hardening before mobile work;
4. live BLE/app integration only after explicit approval.

Default recommendation: Android-first stub if Eric wants mobile progress next, or Windows daemon service wrapper if the lab bridge should become persistent before touching app code.
