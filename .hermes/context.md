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
- `docs/bitchat-app-native-adapter-gate5a.md` — Gates 5A/5B app-native adapter design/skeleton and adapter-backed pump boundary, plus Gate 5D result summary
- `docs/bitchat-app-insertion-points-gate5c.md` — Gate 5C Android/iOS insertion-point mapping
- `docs/APP_ADAPTER_API.md` — Gate 5D platform-neutral app adapter API contract and Android/iOS pseudo-interfaces
- `docs/ios-app-adapter-stub-gate5e.md` — Gate 5E iOS-first disabled/debug app adapter stub plus inbound/outbound hook evidence; local iOS branch/commits and verification boundary
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
- `docs/windows-daemon-scheduled-task.md` — Gate 2I Windows scheduled-task wrapper runbook with dry-run defaults, live `-EnableRealPorts` gate, and log/state paths
- `scripts/windows/Start-MeshCoreBridgeDaemon.ps1` — Windows daemon launcher; defaults to dry-run/no-open and only passes `--open-real-ports` when `-OpenRealPorts` is supplied
- `scripts/windows/Install-MeshCoreBridgeScheduledTask.ps1` — Windows Scheduled Task installer; defaults to dry-run task and only creates a live task when `-EnableRealPorts` is supplied
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

Latest verified result: Gate 2I Windows scheduled-task wrapper is installed and live on `home-pc-atl2`. Local repo tests passed with `python3 -m unittest discover -s tests -v` (99 tests). Desktop Python dependencies were verified/installed (`cryptography 49.0.0`, `pyserial 3.5`). Dry-run scheduled task completed with `LastTaskResult=0` and wrote `mode=dry-run-no-ports-opened`. Live task was registered with `-EnableRealPorts -StartNow`; task State=4/Running, `LastTaskResult=267009` (running), latest JSONL path `C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-183800.jsonl` contains `daemon_plan`, `port_opened` for `COM5`/`pocket1`, and `port_opened` for `COM8`/`pocket2`; latest stderr length was 0 after a 20-second check.

## Approval boundaries

Eric approved taking this project locally to its logical conclusion and approved Gate 1 source-only publication to `redclawanon-rgb/meshcore-bitchat-bridge`; the repo is public at <https://github.com/redclawanon-rgb/meshcore-bitchat-bridge>. Future public posts/releases/tags, hardware purchase/use, real serial/BLE access, secrets, production/security claims, or stock compatibility work still require separate explicit approval.
Do not handle raw secrets in project files.

## Next action

Gate 1 source-only public publication is complete at <https://github.com/redclawanon-rgb/meshcore-bitchat-bridge>. Gates 2C/2D/2E are complete for two MeshCore-flashed WisMesh Pockets on Eric's Windows home desktop. Repo clone is at `C:\\Users\\station1\\meshcore-bitchat-bridge`; Python is `C:\\Users\\station1\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`. `pocket-1`: `COM5`/serial `BAE292D6B7431B72`; `pocket-2`: `COM8`/serial `99EF9E1DC9D17560`; both are flashed to MeshCore USB Companion. Gate 2H daemon state/log/reconnect hardening is complete and live-smoked. Gate 2I Windows scheduled-task wrapper is installed/running live on `home-pc-atl2` with `COM5` and `COM8` opened. Next recommended gate is longer unattended daemon runtime/reporting, unless Eric chooses third Pocket flashing or app/BLE work.
