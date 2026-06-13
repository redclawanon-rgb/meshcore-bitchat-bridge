# Bridge Protocol

## Status

Draft v0. Not implemented yet.

## Candidate carrier

Default candidate: existing MeshCore custom/group data payload, avoiding core MeshCore protocol changes for MVP.

## Bridge frame v0 candidate

```text
magic: 2 bytes       # e.g. BC
version: 1 byte      # 0
flags: 1 byte
msg_type: 1 byte
bridge_id: 4 bytes
message_id: 8 bytes
fragment_index: 1 byte
fragment_count: 1 byte
payload_len: 1 byte
payload: variable
crc16: 2 bytes
```

## Initial message types

- `0x01` HELLO
- `0x02` TEXT_FRAGMENT
- `0x03` ACK
- `0x04` NACK
- `0x05` PEER_ADVERT

## Open protocol questions

- Use `PAYLOAD_TYPE_RAW_CUSTOM` or `PAYLOAD_TYPE_GRP_DATA`?
- CRC16 variant?
- Maximum fragment payload after MeshCore overhead?
- Whether ACKs are bridge-level, MeshCore-level, or both?
