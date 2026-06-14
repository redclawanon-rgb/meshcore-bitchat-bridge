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
- `docs/bitchat-app-native-adapter-gate5a.md` — Gate 5A app-native adapter design/skeleton boundary and next Gate 5B recommendation
- `tools/bridge_frame_codec/bitchat_app_adapter.py` — fixture-backed app-native adapter seam that emits semantic public-text events
- `tools/bridge_frame_codec/bitchat_text.py` — fake semantic bitchat-side public text carrier seam
- `tools/bridge_frame_codec/bridge_pump.py` — no-hardware text bridge pumps: semantic carrier pump plus Gate 5B app-adapter-backed pump
- `tools/bridge_pump_demo.py` — no-hardware bridge pump demo CLI wiring fake MeshCore transport + fake bitchat text carrier
- `tools/no_hardware_smoke.py` — no-hardware smoke transcript script that runs documented demo CLIs locally and summarizes stable JSON fields
- `tests/fixtures/no-hardware-smoke-stable.json` — pinned stable-field fixture for the no-hardware smoke transcript
- `docs/no-hardware-smoke-regression.md` — developer refresh/check note for the no-hardware smoke transcript fixture
- `docs/pre-hardware-readiness.md` — local pre-hardware readiness/operator handoff mapping demos, smoke fixture checks, and `HARDWARE_SMOKE.md`
- `docs/mvp-handoff-index.md` — local MVP handoff/release-readiness index cross-linking protocol, adapter decisions, no-hardware demos, regression fixture, readiness handoff, blockers, and non-claims
- `docs/gated-next-loops.md` — local post-MVP gate playbook map; no gate is active unless Eric explicitly picks one
- `docs/public-release-preflight.md` — Gate 1 public release hygiene checklist with readiness, exact pre-push commands, non-claim wording checklist, stop criteria, and publication record
- `docs/hardware-inventory-preflight.md` — Gate 2A hardware inventory evidence; no candidate serial device visible and no real serial/BLE/hardware access attempted
- `docs/rak4631-target-setup.md` — Gate 2B target setup notes for Eric's loose RAK19003 + RAK4631 assembly with LoRa/BLE antennas and recommended MeshCore USB Serial Companion firmware path
- `docs/wismesh-pocket-gate2c.md` — active Gate 2C target notes for Eric's three RAKwireless WisMesh Pocket units; use one Pocket first and prefer MeshCore RAK4631 USB Companion before guarded real-port smoke
- `README.md` — includes no-hardware demo CLI/smoke usage notes and safety/compatibility boundaries
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
- `tests/test_no_hardware_smoke_cli.py` — no-hardware smoke transcript CLI tests
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

Latest verified result: `python3 -m unittest discover -s tests -v` ran 59 tests in 0.304s and passed. Serial transport remains covered through transport-neutral bridge helpers with fake streams only; serial dry-run still emits no-port-opened packets by default; MVP-15 dry-run replay smoke proves serial TX packet bytes can be extracted and replayed through simulated MeshCore notifications into a fake serial stream/receiver inbox without real port access. MVP-16 inspected public bitchat source and documented a semantic text-only bitchat-side carrier boundary in `BITCHAT_SEAM.md`; MVP-17 implemented a fake in-memory `BitchatTextCarrier` proving decoded `DeliveredText` handoff plus fake carrier-originated public text through the existing MeshCore transport-neutral path; MVP-18 implemented `pump_text_bridge_once`, a no-hardware bridge pump that drains MeshCore-delivered `DeliveredText` into a semantic carrier and forwards carrier-originated public text through `send_text_over_transport`; MVP-19 implemented `tools/bridge_pump_demo.py`, a fake-only bridge pump CLI smoke that prints deterministic both-direction JSON summaries with explicit no-hardware markers; MVP-20 added README usage notes for the no-hardware demo CLIs (`bridge_sim.py`, `bridge_serial.py`, `bridge_pump_demo.py`) with explicit no-serial-by-default/no-BLE/fake-carrier/no-stock-compatibility boundaries; MVP-21 added `tools/no_hardware_smoke.py`, which runs those documented demo CLIs as local subprocesses and emits a stable JSON transcript without opening serial, BLE, hardware, network, secrets, or stock bitchat integration; MVP-22 pinned that stable transcript in `tests/fixtures/no-hardware-smoke-stable.json`, added a fixture comparison test, and documented explicit local refresh/check commands in `docs/no-hardware-smoke-regression.md` and README; MVP-23 added `docs/pre-hardware-readiness.md`, a local operator handoff that maps the no-hardware demos, smoke fixture checks, and gated `HARDWARE_SMOKE.md` sequence before any future hardware use; MVP-24 added `docs/mvp-handoff-index.md` and `docs/gated-next-loops.md`; Gate 1 local-only public release hygiene preflight added `docs/public-release-preflight.md`. No public repository, remote, push, tag, release, package publish, or public post has been performed.

## Approval boundaries

Eric approved taking this project locally to its logical conclusion and approved Gate 1 source-only publication to `redclawanon-rgb/meshcore-bitchat-bridge`; the repo is public at <https://github.com/redclawanon-rgb/meshcore-bitchat-bridge>. Future public posts/releases/tags, hardware purchase/use, real serial/BLE access, secrets, production/security claims, or stock compatibility work still require separate explicit approval.
Do not handle raw secrets in project files.

## Next action

Gate 1 source-only public publication is complete at <https://github.com/redclawanon-rgb/meshcore-bitchat-bridge>. Gates 2C/2D/2E are complete for two MeshCore-flashed WisMesh Pockets on Eric's Windows home desktop/Tailscale SSH path. Repo clone is at `C:\\Users\\station1\\meshcore-bitchat-bridge`; Python is `C:\\Users\\station1\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`. `pocket-1`: `COM5`/serial `BAE292D6B7431B72`; `pocket-2`: `COM8`/serial `99EF9E1DC9D17560`; both are flashed to MeshCore USB Companion. Gate 2H daemon state/log/reconnect hardening is complete: live unplug/replug mapped screen ID `D0521521` to `pocket2`/`COM8`, triggered `serial_read_error`, closed only COM8, retried 8 times while absent, reopened COM8, and post-reconnect delivered `gate2h post reconnect delivery` with `delivered_count=1`, `parse_error_count=0`. Gate 4 scoped bitchat adapter research and Gate 4A/4B/4C/4D/4E fixtures are complete: packet bytes, padding/compression, signing-preimage, deterministic Ed25519, identity TLV, verified-sender acceptance, v2 route layout, fragment payload/reassembly, and packet-ID byte shapes are pinned with no real identity/trust/Noise/BLE/stock compatibility claim. Gates 5A/5B are complete: `BitchatAppAdapter` is the semantic app/native seam, `LocalFixtureBitchatAppAdapter` ingests deterministic fixture packet bytes, dedupes, reassembles fragments, emits public-text events, delegates bridge-delivered text to the existing carrier, and `pump_app_adapter_bridge_once(...)` connects that seam to the local MeshCore bridge pump. Next recommended gate: Gate 5C Android/iOS insertion-point mapping, still design/spike only unless Eric explicitly approves live app/BLE work.
