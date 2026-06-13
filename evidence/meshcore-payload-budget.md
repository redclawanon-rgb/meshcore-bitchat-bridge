# MeshCore Payload Budget Evidence

## Sources inspected

- `meshcore-dev/MeshCore` `docs/packet_format.md` from `main`
- `meshcore-dev/MeshCore` `docs/payloads.md` from `main`
- `meshcore-dev/MeshCore` `docs/companion_protocol.md` from `main`

Inspection date: 2026-06-13

## Key facts

### Radio packet payload

MeshCore v1 packet format is:

```text
[header][transport_codes(optional)][path_length][path][payload]
```

The docs state that `payload` is variable length and up to `MAX_PACKET_PAYLOAD = 184` bytes. Firmware v1.12.0 and older drop payloads larger than 184 bytes.

### Candidate payload types

Relevant MeshCore payload types:

- `PAYLOAD_TYPE_GRP_DATA` (`0x06`) — group datagram, unverified.
- `PAYLOAD_TYPE_MULTIPART` (`0x0A`) — packet is part of a sequence of packets.
- `PAYLOAD_TYPE_RAW_CUSTOM` (`0x0F`) — custom packet, raw bytes, custom encryption.

### Companion channel data path

The companion protocol already exposes channel datagrams:

Send command:

```text
Byte 0:                         0x3E
Byte 1:                         Channel Index (0-7)
Byte 2:                         Path Length (0xFF = flood, otherwise actual path length)
Bytes 3 .. 2+path_len:          Path (omitted when path_len == 0xFF)
Next 2 bytes little-endian:     data_type uint16
Remaining bytes:                Binary payload
```

Important limits:

- `MAX_CHANNEL_DATA_LENGTH = MAX_FRAME_SIZE - 9 = 163` bytes.
- Larger payloads are rejected with `PACKET_ERROR` / `ERR_CODE_ILLEGAL_ARG`.
- `data_type = 0xFFFF` is developer/experimental.
- `0xFF00–0xFFFE` are testing/development values needing no registration.
- Registered app namespaces use `0x0100–0xFEFF` via PR to `docs/number_allocations.md`.

Inbound group datagrams are delivered to the host as `RESP_CODE_CHANNEL_DATA_RECV` (`0x1B`):

```text
Byte 0:                 0x1B
Byte 1:                 SNR scaled ×4
Bytes 2-3:              reserved
Byte 4:                 Channel Index
Byte 5:                 Path Length
Bytes 6-7:              Data Type uint16 little-endian
Byte 8:                 Data Length
Bytes 9 .. 8+data_len:  Payload
```

## MVP decision recommendation

Use MeshCore companion **channel data datagrams** first, i.e. radio-level `PAYLOAD_TYPE_GRP_DATA` and companion command `0x3E`, with `data_type = 0xFFFF` during development.

Reasons:

1. It is already exposed by the companion protocol.
2. Firmware should not need invasive core changes for the first tunnel.
3. The firmware treats the data type as an opaque application namespace.
4. It gives the bridge a usable binary payload budget of 163 bytes through the app/device interface.
5. Later, a registered `data_type` can replace `0xFFFF` if the project becomes real.

## Payload budget for bridge frame v0

Companion channel data payload budget: **163 bytes**.

Current bridge-frame draft overhead:

```text
magic: 2
version: 1
flags: 1
msg_type: 1
bridge_id: 4
message_id: 8
fragment_index: 1
fragment_count: 1
payload_len: 1
crc16: 2
```

Total fixed overhead in the original draft was estimated as 23 bytes. The implemented v0 frame was verified at **22 bytes** fixed overhead because the fixed fields are 20 bytes before payload plus 2 CRC bytes.

Usable fragment body: **163 - 22 = 141 bytes**.

This is enough for short text messages and enough to fragment longer messages. It is not enough for rich bitchat packets without fragmentation.

## Fragmentation requirement

Bridge v0 should assume every application message may need fragmentation.

Minimum reassembly state:

- `bridge_id`
- `message_id`
- `fragment_count`
- received fragment bitmap
- payload bytes per fragment
- expiry timestamp
- duplicate suppression cache

## Risks

- `GRP_DATA` is unverified; bridge must not imply sender authenticity.
- `data_type = 0xFFFF` is development-only and should not be used for a public app namespace long-term.
- The 163-byte companion limit is stricter than the 184-byte radio payload limit.
- Airtime and queue pressure will matter quickly if many fragmented messages are sent.
- ACK/retry policy must be conservative to avoid flooding LoRa.

## Next step

Update `PROTOCOL.md` to lock v0 around a 163-byte frame budget and 141-byte max fragment body, then implement a local codec test harness.
