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

Latest verified result: COM5 and COM8 were aligned to the iPhone/COM10 MeshCore Bluetooth radio settings shown by Eric: USA/Canada preset, freq 910.525 MHz, BW 62.5 kHz, SF 7, CR 5. Using CMD_APP_START/SELF_INFO, COM5 and COM8 were first at 915.0 MHz, BW 62.5, SF 8, CR 5. Sent CMD_SET_RADIO to both with freq=910.525, BW=62.5, SF=7, CR=5; both verified true afterward (COM5 name C8BB12CB, COM8 name D0521521). Both were rebooted, then 4-message COM5<->COM8 stability delivered 4/4, avg latency ~0.652s, no duplicates, no parse errors. Persistent daemon was restarted; latest log `C:\\Users\\station1\\AppData\\Local\\MeshCoreBitchatBridge\\logs\\meshcore-bridge-20260614-205317.jsonl` opened COM5/COM8, stderr length 0, State=Running/267009; watchdog check passed and cron f33031865d0a resumed. Eric then sent an iPhone/COM10 MeshCore text to both; daemon log showed RF activity and `msg_waiting` on both pocket1/COM5 and pocket2/COM8, then `CMD_SYNC_NEXT_MESSAGE` returned `unknown_0x07` frames containing ASCII `Test from 3` on each, plus `unknown_0x81` follow-up frames. Commit `1d24403` adds stock MeshCore text decoding: 0x07/0x08/0x10/0x11 are classified as contact/channel text messages, parsed into `meshcore_text_message` JSONL events with `text`, `pubkey_prefix`/`channel_idx`, timestamp, path metadata, and `txt_type`; 0x81 is classified as `path_update`. Local suite passed 104 tests. Windows repo was reset to `origin/main` at `1d24403`; focused parser tests passed on home-pc-atl2; recorded payload smoke decoded both previous iPhone frames as `contact_msg_recv` text `Test from 3`. Daemon was restarted at log `C:\\Users\\station1\\AppData\\Local\\MeshCoreBitchatBridge\\logs\\meshcore-bridge-20260614-210412.jsonl`, opened COM5/COM8, stderr length 0, State=Running/267009; watchdog check passed and cron f33031865d0a resumed. Eric sent another iPhone/COM10 message after decoder deployment; live log produced two `meshcore_text_message` events: pocket2/COM8 text `Second test from iphone connection ` and pocket1/COM5 text `Second test from iphone connection ??` (raw payload ends `f09f918d`, emoji rendered as `??` by the PowerShell display). This confirms the deployed daemon now emits readable stock MeshCore text events from live iPhone sends. COM10 remains MeshCore Bluetooth/iPhone firmware and is not part of the USB Companion daemon unless Eric explicitly asks to reconfigure/flash it.

## Approval boundaries

Eric approved taking this project locally to its logical conclusion and approved Gate 1 source-only publication to `redclawanon-rgb/meshcore-bitchat-bridge`; the repo is public at <https://github.com/redclawanon-rgb/meshcore-bitchat-bridge>. Future public posts/releases/tags, hardware purchase/use, real serial/BLE access, secrets, production/security claims, or stock compatibility work still require separate explicit approval.
Do not handle raw secrets in project files.

## Next action

Gate 1 source-only public publication is complete at <https://github.com/redclawanon-rgb/meshcore-bitchat-bridge>. Gates 2C/2D/2E are complete for two MeshCore-flashed WisMesh Pockets on Eric's Windows home desktop. Repo clone is at `C:\\Users\\station1\\meshcore-bitchat-bridge`; Python is `C:\\Users\\station1\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`. `pocket-1`: `COM5`/serial `BAE292D6B7431B72`; `pocket-2`: `COM8`/serial `99EF9E1DC9D17560`; both are flashed to MeshCore USB Companion. Gate 2H daemon state/log/reconnect hardening is complete and live-smoked. Gate 2I Windows scheduled-task wrapper is installed/running live on `home-pc-atl2` with `COM5` and `COM8` opened, a 60-minute passive live watch passed with no daemon-side errors, watchdog job `f33031865d0a` is active, and active scheduled-task message smoke passed. Next recommended gate is third Pocket flashing/inventory or app/BLE work.
