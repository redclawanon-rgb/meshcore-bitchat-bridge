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
- `ADAPTER.md` — live transport adapter decision/seam
- `BITCHAT_SEAM.md` — public bitchat source inspection and text-only future carrier boundary
- `tools/bridge_frame_codec/bitchat_text.py` — fake semantic bitchat-side public text carrier seam
- `tools/bridge_frame_codec/bridge_pump.py` — no-hardware text bridge pump between MeshCore delivered text and fake/semantic bitchat carrier
- `tools/bridge_pump_demo.py` — no-hardware bridge pump demo CLI wiring fake MeshCore transport + fake bitchat text carrier
- `README.md` — includes no-hardware demo CLI usage notes and safety/compatibility boundaries
- `evidence/meshcore-payload-budget.md` — MeshCore payload budget evidence
- `tools/bridge_frame_codec/` — local Python bridge-frame/message/MeshCore companion codec
- `tools/bridge_frame_codec/transport.py` — transport-neutral companion datagram seam + fake transport
- `tools/bridge_frame_codec/serial_adapter.py` — no-hardware MeshCore serial packet wrapper/parser/replay extraction helper + no-open serial transport skeleton
- `HARDWARE_SMOKE.md` — gated hardware smoke checklist; no real port use without explicit Eric invocation
- `tools/bridge_cli.py` — local encode/decode CLI harness
- `tools/bridge_sim.py` — no-hardware simulator demo CLI
- `tools/bridge_serial.py` — serial dry-run CLI, no port opened unless explicit `--open-real-port`
- `tests/test_bridge_frame_codec.py` — frame codec/unit tests
- `tests/test_bridge_message.py` — text message helper tests
- `tests/test_bridge_cli.py` — local CLI tests
- `tests/test_meshcore_companion.py` — MeshCore companion wrapper tests
- `tools/bridge_frame_codec/sim.py` — no-hardware two-node simulator
- `tests/test_bridge_sim.py` — simulator end-to-end tests
- `tests/test_bridge_sim_cli.py` — simulator CLI tests
- `tests/test_bridge_transport.py` — fake transport tests
- `tests/test_bitchat_text.py` — fake bitchat-side semantic text carrier tests
- `tests/test_bridge_pump.py` — fake-only no-hardware bridge pump tests
- `tests/test_bridge_pump_demo_cli.py` — bridge pump no-hardware demo CLI tests
- `tests/vectors/bridge-frame-v0.json` — canonical v0 test vector

## Current MVP scope

In scope:

- MeshCore companion channel data datagram tunnel
- tiny bridge-frame protocol
- codec and fragmentation tests
- local CLI bridge harness
- local no-hardware two-node simulator
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

Use a transport-neutral companion-datagram seam for live adapters. First live adapter target is serial, then BLE. Details are in `ADAPTER.md`.

## Verification command

```bash
python3 -m unittest discover -s tests -v
```

Latest verified result: 56 tests passed; serial transport covered through transport-neutral bridge helpers with fake streams only; serial dry-run still emits no-port-opened packets by default; MVP-15 dry-run replay smoke proves serial TX packet bytes can be extracted and replayed through simulated MeshCore notifications into a fake serial stream/receiver inbox without real port access. MVP-16 inspected public bitchat source and documented a semantic text-only bitchat-side carrier boundary in `BITCHAT_SEAM.md`; MVP-17 implemented a fake in-memory `BitchatTextCarrier` proving decoded `DeliveredText` handoff plus fake carrier-originated public text through the existing MeshCore transport-neutral path; MVP-18 implemented `pump_text_bridge_once`, a no-hardware bridge pump that drains MeshCore-delivered `DeliveredText` into a semantic carrier and forwards carrier-originated public text through `send_text_over_transport`; MVP-19 implemented `tools/bridge_pump_demo.py`, a fake-only bridge pump CLI smoke that prints deterministic both-direction JSON summaries with explicit no-hardware markers; MVP-20 added README usage notes for the no-hardware demo CLIs (`bridge_sim.py`, `bridge_serial.py`, `bridge_pump_demo.py`) with explicit no-serial-by-default/no-BLE/fake-carrier/no-stock-compatibility boundaries. No stock compatibility claim is made.

## Approval boundaries

Eric approved taking this project locally to its logical conclusion: continue local implementation, tests, docs, and commits through the MVP path without asking before each bounded loop.
Do not push public repos, post publicly, buy/order hardware, access secrets, or claim production security without separate explicit approval.
Do not handle raw secrets in project files.

## Next action

Run MVP-21: add a tiny no-hardware examples/smoke transcript or script that runs the documented demo CLIs and captures stable JSON fields, so README examples stay drift-resistant. Keep it local/text-only/no-hardware/no-network; do not open serial unless explicitly invoked with `--open-real-port` after approval, do not use BLE, and do not claim stock bitchat compatibility.
