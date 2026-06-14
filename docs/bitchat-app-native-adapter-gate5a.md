# Gate 5A — App-native bitchat adapter design

## Status

Gate 5A is a local design-and-skeleton gate. It does not open BLE, serial ports, mobile apps, hardware, secrets, network APIs, or stock bitchat sessions.

The selected first implementation path is:

1. keep the MeshCore bridge core transport-neutral;
2. define an app-native bitchat adapter boundary in Python;
3. prove the boundary with deterministic Gate 4 packet fixtures;
4. only later map the boundary to Android/iOS insertion points.

## Why this gate exists

Gates 4A–4E pinned local byte shapes for public messages, padding/compression, signing preimages, deterministic Ed25519 fixtures, identity announcements, verified-sender acceptance simulation, v2 routes, fragment payloads, reassembly, and packet IDs.

Those fixtures are enough to design the seam between the bridge and a real bitchat integration. They are not enough to claim stock app interoperability. Gate 5A prevents the project from bolting fixture code directly into the MeshCore daemon or pretending a Python process can become a stock BLE bitchat peer.

## Adapter boundary

A future app-native adapter should satisfy this shape:

```text
bitchat app/native callbacks or service API
        |
        v
BitchatAppAdapter.ingest_packet_bytes(data) -> [BitchatAppPublicTextEvent]
        |
        v
MeshCore bridge text/transport layer
```

And for the opposite direction:

```text
MeshCore bridge delivered public text
        |
        v
BitchatAppAdapter.publish_bridge_text(text, from_bridge_id, message_id)
        |
        v
bitchat app/native public-text API
```

The bridge core should receive semantic public-text events, not BLE callbacks, Noise internals, mobile lifecycle state, or app UI state.

## Local skeleton

Implemented file:

```text
tools/bridge_frame_codec/bitchat_app_adapter.py
```

Exported types:

- `BitchatAppAdapter`
- `BitchatAppAdapterError`
- `BitchatAppPublicTextEvent`
- `LocalFixtureBitchatAppAdapter`

`BitchatAppPublicTextEvent` carries:

- `text`
- `packet_id_hex`
- `sender_id`
- `timestamp_ms`
- optional `route`
- `source = "fixture"` for this local implementation

`LocalFixtureBitchatAppAdapter` can:

- ingest raw/wire bytes decodable by the Gate 4 fixture decoder;
- emit semantic public-text events for public `MESSAGE` packets;
- dedupe packets by the observed sync packet ID;
- buffer fragment packets by fragment ID;
- ignore exact duplicate fragment packets;
- reassemble complete fragment sets and recursively adapt the original packet bytes;
- publish bridge-delivered text by delegating to the existing semantic `BitchatTextCarrier`.

## Tests

Implemented file:

```text
tests/test_bitchat_app_adapter.py
```

Coverage:

- raw public message fixture bytes emit one semantic event;
- duplicate packet bytes emit no second event;
- bridge-delivered text delegates to the existing semantic carrier;
- routed v2 fragment packets reassemble before emitting the original public-text event;
- exact duplicate fragments are ignored until the complete fragment set arrives.

Verification:

```text
python3 -m unittest tests.test_bitchat_app_adapter -v
Ran 4 tests in 0.001s
OK
```

## Chosen architecture direction

Use a **local Python adapter boundary first**, then map it to an app-native integration.

Reasoning:

- It keeps MeshCore daemon code independent from stock app internals.
- It lets the existing deterministic fixtures drive interface design.
- It avoids claiming live stock compatibility before BLE/mobile lifecycle proof.
- It gives Android/iOS work a concrete contract instead of vague integration goals.

## Future Android insertion-point questions

A later Android gate should inspect and decide where an app-native adapter would hook into:

- inbound packet decode/receive pipeline;
- outbound public-message send API;
- identity/verified peer registry callbacks;
- fragment/reassembly manager callbacks;
- sync/dedup packet tracking;
- BLE lifecycle and permissions boundary.

The app should own BLE, Noise, route planning, trust UI, lifecycle, and persistence. The bridge should receive/send semantic public text through the adapter contract.

## Future iOS insertion-point questions

A later iOS gate should inspect and decide where an app-native adapter would hook into:

- `BinaryProtocol` / `BitFoundation` packet surfaces;
- BLE receive pipeline;
- `BLEFragmentHandler` and assembly buffer;
- public-message model callbacks;
- identity/trust verification services;
- outbound public text publishing API.

The same ownership rule applies: iOS owns BLE, Noise, route planning, trust UI, lifecycle, and persistence; the bridge owns MeshCore transport and text-event forwarding.

## Explicit non-claims

Gate 5A does not implement or prove:

- BLE discovery or advertising;
- BLE stream assembly;
- real mobile app callbacks;
- Noise sessions;
- route-planning correctness;
- trust UI or persistence;
- live stock app interoperability;
- production security;
- real hardware/radio delivery.

It only defines and tests a local app-native adapter contract using deterministic fixture bytes.

## Gate 5B result — adapter-backed no-hardware bridge pump

Gate 5B integrated the app-adapter seam into the local bridge pump without removing the older semantic-carrier pump.

Implemented in:

```text
tools/bridge_frame_codec/bridge_pump.py
```

New exported types/functions:

- `AppAdapterBridgePumpResult`
- `pump_app_adapter_bridge_once(...)`

The new pump pass moves data in three deterministic no-hardware steps:

1. drain queued MeshCore companion notifications from the transport into the local bridge node;
2. publish decoded `DeliveredText` into `BitchatAppAdapter.publish_bridge_text(...)`;
3. ingest fixture-backed app/native packet bytes through `BitchatAppAdapter.ingest_packet_bytes(...)` and forward emitted public-text events through `send_text_over_transport(...)`.

Implemented tests:

```text
tests/test_bitchat_app_adapter_pump.py
```

Coverage:

- MeshCore-delivered text is published through the app-adapter seam;
- a fixture-backed app public-message packet is forwarded to MeshCore transport;
- a combined pass can publish MeshCore text to the adapter while reassembling and forwarding a routed fragmented v2 app event;
- duplicate app packet bytes do not forward twice.

Verification:

```text
python3 -m unittest tests.test_bitchat_app_adapter_pump -v
Ran 4 tests in 0.001s
OK
```

Gate 5B is still fixture-only. It does not open BLE, serial ports, mobile apps, hardware, or stock bitchat sessions.

## Recommended next gate

Gate 5C should map the app-adapter contract to Android/iOS insertion points as a design/spike gate:

- Android receive/send/fragment/dedup/trust callback points;
- iOS `BitFoundation`/BLE receive/fragment/trust callback points;
- event ownership boundaries for BLE, Noise, route planning, trust UI, lifecycle, and persistence;
- minimal app-side API shape that could feed `BitchatAppAdapter` without making the MeshCore bridge own mobile internals.

Live Android/iOS integration should wait until Gate 5C identifies the least-invasive insertion point.
