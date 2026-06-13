# MeshCore ↔ bitchat Bridge Context

## Purpose

Build an MVP bridge that can carry bitchat-like text messages over MeshCore/LoRa using a custom bridge-frame tunnel.

## Project root

`/home/openclaw/projects/meshcore-bitchat-bridge`

## Current source of truth

- `README.md` — project overview
- `DESIGN.md` — architecture approach
- `PROTOCOL.md` — bridge frame v0 protocol
- `THREAT_MODEL.md` — security posture
- `LOOPS.md` — development loop protocol
- `STATUS.md` — current state and next action
- `DECISIONS.md` — decisions and pending gates
- `evidence/meshcore-payload-budget.md` — MeshCore payload budget evidence
- `tools/bridge_frame_codec/` — local Python bridge-frame/message codec
- `tools/bridge_cli.py` — local encode/decode CLI harness
- `tests/test_bridge_frame_codec.py` — frame codec/unit tests
- `tests/test_bridge_message.py` — text message helper tests
- `tests/test_bridge_cli.py` — local CLI tests
- `tests/vectors/bridge-frame-v0.json` — canonical v0 test vector

## Current MVP scope

In scope:

- MeshCore companion channel data datagram tunnel
- tiny bridge-frame protocol
- codec and fragmentation tests
- local CLI bridge harness
- Python bridge harness
- two-node text demo

Out of scope for MVP:

- full stock bitchat compatibility
- private DMs
- Noise tunneling
- Nostr
- images/files
- production security claims

## Current technical decision

Use MeshCore companion channel data datagrams first:

- companion command: `0x3E`
- radio payload: `PAYLOAD_TYPE_GRP_DATA` (`0x06`)
- development data type: `0xFFFF`
- companion binary payload limit: 163 bytes
- bridge frame fixed overhead: 22 bytes
- max v0 fragment body: 141 bytes
- CRC: CRC-16/XMODEM stored little-endian

## Verification command

```bash
python3 -m unittest discover -s tests -v
```

Latest verified result: 19 tests passed.

## Approval boundaries

Eric approved taking this project locally to its logical conclusion: continue local implementation, tests, docs, and commits through the MVP path without asking before each bounded loop.
Do not push public repos, post publicly, buy/order hardware, access secrets, or claim production security without separate explicit approval.
Do not handle raw secrets in project files.

## Next action

Run MVP-07: add local MeshCore companion channel-data frame builder/parser around bridge frames, without hardware/BLE yet.
