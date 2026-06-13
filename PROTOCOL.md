# Bridge Protocol

## Status

Bridge frame v0 locked for local codec implementation. Not hardware-tested yet.

## MeshCore carrier for MVP

Use MeshCore companion **channel data datagrams** first.

- Companion send command: `0x3E`
- Radio payload type: `PAYLOAD_TYPE_GRP_DATA` (`0x06`)
- Development `data_type`: `0xFFFF`
- Long-term `data_type`: register an application/community namespace if the project becomes public
- Companion binary payload limit: **163 bytes**

This avoids invasive MeshCore firmware protocol changes for the first MVP tunnel. The bridge payload is opaque to MeshCore firmware.

## Bridge frame v0

All integer fields are little-endian. Total fixed overhead is **22 bytes**, leaving **141 bytes** for `payload` inside the 163-byte MeshCore companion channel-data limit.

```text
Offset  Size  Field
0       2     magic: ASCII "BB" (`0x42 0x42`), short for bitchat bridge
2       1     version: `0x00`
3       1     flags
4       1     msg_type
5       4     bridge_id: uint32 little-endian
9       8     message_id: uint64 little-endian
17      1     fragment_index: zero-based
18      1     fragment_count: total fragments, 1-255
19      1     payload_len: 0-140
20      N     payload bytes
20+N    2     crc16_xmodem over bytes 0..19+N
```

## Constants

```text
MESHCORE_CHANNEL_DATA_MAX = 163
BRIDGE_FRAME_FIXED_OVERHEAD = 22
BRIDGE_FRAME_MAX_PAYLOAD = 141
BRIDGE_MAGIC = 0x42 0x42
BRIDGE_VERSION = 0
CRC = CRC-16/XMODEM, initial value 0x0000, polynomial 0x1021
```

## Message types

```text
0x01 HELLO
0x02 TEXT_FRAGMENT
0x03 ACK
0x04 NACK
0x05 PEER_ADVERT
```

## Flags

```text
0x01 WANT_ACK
0x02 IS_ACK_RESPONSE
0x04 RESERVED_ENCRYPTED
0x08 RESERVED_SIGNED
0x10-0x80 reserved
```

Unknown flags are not fatal for parsing, but implementations should not act on unknown flags.

## Fragmentation rules

- `fragment_count` must be `1..255`.
- `fragment_index` must be `< fragment_count`.
- `payload_len` must match actual payload byte count.
- Message reassembly key is `(bridge_id, message_id, msg_type)`.
- Duplicate fragments with identical bytes are ignored.
- Duplicate fragments with conflicting bytes are rejected.
- Reassembly state should expire; local codec tests use deterministic expiry hooks later.
- MVP sends text as UTF-8 split across `TEXT_FRAGMENT` payloads.

## ACK/NACK rules for MVP

MVP codec defines ACK/NACK frames but transport-level retry is deferred until hardware/queue behavior is measured.

ACK payload draft:

```text
acked_message_id: uint64 little-endian
highest_contiguous_fragment: uint8
received_bitmap: variable bitset, LSB-first per byte
```

NACK payload draft:

```text
nacked_message_id: uint64 little-endian
reason_code: uint8
optional details: variable
```

## Validation rules

A decoder must reject:

- frame shorter than 22 bytes,
- wrong magic,
- unsupported version,
- payload length greater than 141,
- payload length not matching frame length,
- `fragment_count == 0`,
- `fragment_index >= fragment_count`,
- CRC mismatch.

## MVP security note

Bridge frame v0 provides framing integrity only. CRC is for accidental corruption, not adversarial tamper resistance. MVP text mode remains lab-only and must not be presented as preserving bitchat's end-to-end security model.
