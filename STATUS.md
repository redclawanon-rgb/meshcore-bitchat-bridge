# Status

## Current state

Local-first development is underway. Bridge frame v0 is locked, local codec is implemented, message-level UTF-8 text fragmentation/reassembly helpers are implemented, a local CLI harness can encode/decode frames without hardware, MeshCore companion channel-data command/notification wrappers are implemented locally, a no-hardware two-node simulator proves end-to-end text exchange over the local stack, a simulator demo CLI prints deterministic A ↔ B exchange summaries, a transport-neutral companion datagram seam has a fake transport harness, a no-hardware serial adapter scaffold/dry-run CLI emits exact MeshCore serial packet bytes, the serial companion datagram transport is exercised through the transport-neutral bridge path with fake streams only, a no-hardware orchestration smoke replays serial dry-run TX packet bytes through the simulator/fake-stream receiver path, the bitchat-side public-text seam has been inspected/designed as a semantic text-only carrier boundary without stock compatibility claims, a fake in-memory `BitchatTextCarrier` proves decoded bridge text handoff plus carrier-originated text forwarding through the existing MeshCore transport-neutral path, a tiny no-hardware bridge pump now orchestrates both directions in one text-only pass, a bridge pump demo CLI prints deterministic fake-only JSON summaries for operator sanity checks, README usage notes now document all no-hardware demo CLIs with explicit no-serial/no-BLE/fake-carrier/no-stock-compatibility boundaries, a drift-resistant no-hardware smoke transcript script runs the documented demo CLIs as local subprocesses and captures stable JSON fields without opening hardware/network paths, the no-hardware smoke transcript stable fields are pinned in a developer regression fixture with explicit local refresh/check instructions, a local pre-hardware readiness/operator handoff note maps the demos, smoke transcript fixture, and gated hardware checklist into an exact pre-hardware sequence, and a local MVP handoff/release-readiness index now cross-links protocol, adapter decisions, no-hardware demos, smoke regression, pre-hardware readiness, blockers, and non-claims for a future human operator.

## Verified

- Local git repo initialized.
- Project OS files created.
- MeshCore docs inspected from GitHub `main`:
  - `docs/packet_format.md`
  - `docs/payloads.md`
  - `docs/companion_protocol.md`
- Evidence written to `evidence/meshcore-payload-budget.md`.
- `PROTOCOL.md` locked bridge frame v0 around MeshCore companion channel data datagrams.
- Test vector created at `tests/vectors/bridge-frame-v0.json`.
- Python codec implemented at `tools/bridge_frame_codec/`.
- Text helpers implemented in `tools/bridge_frame_codec/message.py`.
- Local CLI implemented at `tools/bridge_cli.py`.
- MeshCore companion wrapper implemented at `tools/bridge_frame_codec/meshcore_companion.py`.
- No-hardware two-node simulator implemented at `tools/bridge_frame_codec/sim.py`.
- Simulator demo CLI implemented at `tools/bridge_sim.py`.
- Simulator tests implemented at `tests/test_bridge_sim.py`.
- Simulator CLI tests implemented at `tests/test_bridge_sim_cli.py`.
- Adapter path decision documented at `ADAPTER.md`.
- Decision `D004` added: transport-neutral seam, serial first, BLE second.
- Transport seam implemented at `tools/bridge_frame_codec/transport.py`.
- Fake transport tests implemented at `tests/test_bridge_transport.py`.
- Serial packet scaffold implemented at `tools/bridge_frame_codec/serial_adapter.py`.
- `SerialCompanionDatagramTransport` skeleton implemented with default no-open behavior and fake byte-stream test coverage.
- `SerialCompanionDatagramTransport` covered through `send_text_over_transport`/`drain_transport_to_node` using an in-memory serial byte stream only.
- Serial dry-run CLI implemented at `tools/bridge_serial.py`.
- Serial CLI real-port path now requires explicit `--open-real-port`; dry-run remains no-open by default.
- Serial adapter tests implemented at `tests/test_serial_adapter.py`.
- Serial dry-run replay helper implemented via `unwrap_serial_tx_packet`, proving dry-run TX bytes can be validated/extracted without opening a port.
- MVP-15 no-hardware orchestration smoke test proves text -> serial dry-run TX packet bytes -> extracted companion command -> simulated MeshCore notification -> fake serial stream -> receiver inbox.
- Gated hardware smoke checklist drafted at `HARDWARE_SMOKE.md`; real serial access remains behind explicit Eric invocation and `--open-real-port`/`open_real_port=True`.
- Public bitchat repository inspected from GitHub `main` for app-level transport, BLE public-message, packet, message type, and inbound public-message seams.
- `BITCHAT_SEAM.md` documents the MVP bitchat-side boundary: decoded bridge text <-> future semantic public-text carrier, with no stock compatibility claim.
- Decision `D005` added: semantic text-only bitchat-side MVP seam; do not forge stock `BitchatPacket` bytes for MVP.
- Fake bitchat-side text carrier seam implemented at `tools/bridge_frame_codec/bitchat_text.py` with semantic text-only `BitchatTextCarrier`, `BitchatPublishedText`, `BitchatOutboundText`, and `FakeBitchatTextCarrier`.
- Fake bitchat text carrier tests implemented at `tests/test_bitchat_text.py`, proving decoded `DeliveredText` handoff and fake carrier-originated public text through existing MeshCore transport-neutral helpers.
- No-hardware bridge pump helper implemented at `tools/bridge_frame_codec/bridge_pump.py` with `pump_text_bridge_once` and `BridgePumpResult`, draining MeshCore-delivered `DeliveredText` into a `BitchatTextCarrier` and forwarding carrier-originated public text through `send_text_over_transport`.
- Fake-only bridge pump tests implemented at `tests/test_bridge_pump.py`, proving MeshCore -> carrier, carrier -> MeshCore, combined-direction counts, and fragmented carrier-originated sends without hardware/BLE/serial opens/stock packet forging.
- No-hardware bridge pump demo CLI implemented at `tools/bridge_pump_demo.py`, wiring `FakeCompanionDatagramTransport` + `FakeBitchatTextCarrier` through `pump_text_bridge_once` and printing deterministic JSON summaries with no-hardware safety markers.
- Bridge pump demo CLI tests implemented at `tests/test_bridge_pump_demo_cli.py`, verifying deterministic both-direction output, fake/no-hardware markers, carrier published messages, receiver inbox, and fragmented carrier-originated forwarding summaries.
- MVP-20 README usage notes added for `tools/bridge_sim.py`, `tools/bridge_serial.py`, and `tools/bridge_pump_demo.py`, including expected JSON summaries and safety/compatibility boundaries: no serial opened by default, no BLE, fake/simulated transport and carrier paths, no stock bitchat compatibility or production-security claims.
- MVP-21 no-hardware smoke transcript script added at `tools/no_hardware_smoke.py`, running the three documented demo CLIs via local subprocesses and summarizing stable JSON fields with explicit no-serial/no-BLE/no-network/no-real-hardware markers.
- Smoke transcript CLI tests added at `tests/test_no_hardware_smoke_cli.py`, verifying documented commands, stable output fields, dry-run serial mode, and fake/no-hardware safety markers.
- MVP-22 no-hardware smoke regression fixture added at `tests/fixtures/no-hardware-smoke-stable.json`, with `tests/test_no_hardware_smoke_cli.py` comparing the full stable transcript to the fixture.
- Developer refresh/check note added at `docs/no-hardware-smoke-regression.md`, and README now points to the fixture, local check command, intentional refresh command, and no cron/nudge/autoloop boundary.
- MVP-23 local pre-hardware readiness/operator handoff note added at `docs/pre-hardware-readiness.md`, mapping the no-hardware demo CLIs, smoke transcript fixture/check commands, and gated `HARDWARE_SMOKE.md` checklist into an exact sequence before any future hardware use.
- MVP-24 local MVP handoff/release-readiness index added at `docs/mvp-handoff-index.md`, cross-linking `PROTOCOL.md`, adapter decisions, no-hardware demos, the smoke regression fixture/note, pre-hardware readiness, `HARDWARE_SMOKE.md`, current blockers, and non-claims without opening serial/BLE/hardware/network paths or adding automation.
- Post-MVP gated next-loop playbook added at `docs/gated-next-loops.md`, mapping trigger/authorization, preflight checks, bounded steps, verification/evidence, stop/rollback criteria, and likely affected files for public repo prep, hardware smoke, real serial adapter smoke, BLE exploration, stock bitchat compatibility research, secrets handling, and production/security review. No gated path is active unless Eric explicitly picks one.
- Gate 1 local-only public release hygiene preflight added at `docs/public-release-preflight.md`, recording current readiness, exact pre-push commands, required target details still needed, non-claim wording checklist, stop criteria, and an explicit no-public-action-performed note. Public repository creation, remote setup, push, tag, release, package publish, issue/wiki/discussion settings, and public posting remain unperformed and gated.
- Gate 4 scoped bitchat-side adapter research completed in `docs/bitchat-adapter-research-gate4.md`, pinning current iOS upstream `permissionlesstech/bitchat` commit `bbe1ed0652a5f8435accdf0ef44b028409ceab7e` and Android upstream `permissionlesstech/bitchat-android` commit `13585a9a9caf1687dec66535f78e0d918e690585`, documenting public text send/receive seams, packet/BLE constants, license differences, and the recommendation to do packet conformance fixtures before any live stock-BLE work.
- Decision `D006` added: after the proven MeshCore daemon, the next bitchat-side step should be version-pinned packet conformance fixtures/tests, not a Python daemon pretending to be a stock bitchat BLE peer.
- Gate 4A packet conformance fixtures implemented at `tools/bridge_frame_codec/bitchat_packet_fixture.py`, exported from `tools/bridge_frame_codec/__init__.py`, and covered by `tests/test_bitchat_packet_fixture.py`; tests pin deterministic raw unpadded v1 public `MESSAGE` fixture bytes for the iOS-observed no-recipient shape and the Android-observed broadcast-recipient shape, preserve/reject signature length structurally, and explicitly reject compressed/route-flagged packets as out of scope.
- Gate 4B expanded packet fixtures to cover upstream-observed PKCS#7-style padding, raw-deflate compression with v1 original-size prefix, raw-first/unpad decode fallback, and signing-preimage shape with TTL fixed to `SYNC_TTL_HOPS = 0` and signature removed. These remain fixture-only: no signing, signature verification, Noise, BLE, peer authenticity, or stock compatibility claim.
- Decision `D008` added: padding/compression/preimage fixtures are allowed for deterministic conformance tests only, while real identity/signing/verification/BLE/app lifecycle remain separate future gates.
- Gate 4C identity/signature fixtures implemented at `tools/bridge_frame_codec/bitchat_identity_fixture.py`, exported from `tools/bridge_frame_codec/__init__.py`, and covered by `tests/test_bitchat_identity_fixture.py`; deterministic non-secret Ed25519 seed/public-key/signature fixtures cover upstream-observed packet signing preimage bytes, iOS canonical announce binding bytes, and iOS/Android identity-announcement TLV shape.
- Decision `D009` added: deterministic Ed25519 fixtures are allowed for local byte-shape tests only, not real device identity, trust establishment, Noise authentication, verified peer registry behavior, BLE interoperability, or stock bitchat compatibility.
- Gate 4D verified-sender acceptance simulation implemented in `VerifiedSenderFixtureRegistry`: signed identity announces register peer nickname/noise/signing keys, and signed public messages are accepted only after a verified announce and signature verification against the registered key.
- Decision `D010` added: verified-sender simulation is a deterministic local acceptance-policy fixture only, not BLE discovery, Noise sessions, app lifecycle, persistence, trust UX/policy edge cases, mobile peer-registry behavior, or stock compatibility.
- Gate 4E v2/route/fragment fixtures implemented: `BitchatPacketFixture` now supports v2 4-byte payload lengths and route count/hops, `BitchatFragmentPayloadFixture` covers 13-byte fragment payload headers, fragment reassembly fixtures reconstruct original packet bytes, and packet ID fixtures pin SHA-256(type|sender|timestamp|payload)[:16].
- Decision `D011` added: v2/route/fragment support is fixture-only and does not claim live relay behavior, BLE stream assembly, route planning, transfer scheduling, Noise/session routing, mobile lifecycle, or stock compatibility.
- Gate 5A app-native adapter boundary implemented in `tools/bridge_frame_codec/bitchat_app_adapter.py`: `BitchatAppAdapter` defines the future app/native seam, `LocalFixtureBitchatAppAdapter` ingests deterministic packet fixture bytes, dedupes by packet ID, reassembles fragments, emits semantic public-text events, and delegates bridge-delivered text to the existing semantic carrier.
- Gate 5A design doc added at `docs/bitchat-app-native-adapter-gate5a.md`; Decision `D012` added: prove the app-native adapter contract locally before Android/iOS live insertion points, while keeping BLE, Noise, lifecycle, route planning, trust UI, and persistence owned by future app-native layers.
- Gate 5B adapter-backed no-hardware pump implemented in `tools/bridge_frame_codec/bridge_pump.py`: `pump_app_adapter_bridge_once(...)` drains MeshCore-delivered text into `BitchatAppAdapter.publish_bridge_text(...)`, ingests fixture-backed app packet bytes, and forwards emitted public-text events over the existing MeshCore transport-neutral send path.
- Gate 5B tests added at `tests/test_bitchat_app_adapter_pump.py`; Decision `D013` added: adapter-backed pump integration is local fixture-only and does not open BLE, serial ports, mobile apps, hardware, or stock bitchat sessions.
- Gate 5C Android/iOS insertion-point mapping added at `docs/bitchat-app-insertion-points-gate5c.md`; Decision `D014` added: future live app work should subscribe to verified semantic public-text events after app acceptance policy and publish bridge text through existing app public-send APIs, not raw BLE/BinaryProtocol hooks.
- Gate 5D platform-neutral app adapter API spec added at `docs/APP_ADAPTER_API.md`; Decision `D015` added: Android/iOS adapters should emit accepted semantic `VerifiedPublicTextEvent` records and publish MeshCore text through existing app public-send paths. `BitchatAppPublicTextEvent` now includes backward-compatible optional `nickname`, `app_message_id`, `platform`, and `accepted` fields.
- Gate 5E iOS-first disabled/debug app adapter stub added in local iOS checkout `/tmp/bitchat-ios` on branch `gate5e-ios-adapter-stub`, commits `dfdcd6f`, `72fdf18`, `44bb8b0`, and `72cb7f4`; bridge record added at `docs/ios-app-adapter-stub-gate5e.md`; Decisions `D016`, `D017`, and `D018` added. The iOS stub is not connected to any live bridge transport; inbound hook defaults no-op, outbound wrapper defaults `.adapterDisabled`, and `MeshBridgeDebugAdapterConfiguration.disabled` is the explicit fully-off config owner. MacBook verification staged the checkout at `/Users/ericdecker/Developer/bitchat-ios-gate5e`; full Xcode/SwiftPM build is blocked there by macOS 11/Xcode 13.2.1 vs project Swift tools 5.9/newer `.xcodeproj` object types, but modified app source files pass direct `swiftc -parse` checks.
- Bridge-side iOS debug config fixture added at `tools/bridge_frame_codec/ios_debug_adapter_fixture.py` with tests at `tests/test_ios_debug_adapter_fixture.py`; it executes disabled, inbound-only, outbound-only, fully-enabled, and over-length rejection behavior without claiming iOS runtime/BLE/radio delivery.
- Gate 2I Windows daemon scheduled-task wrapper added: `scripts/windows/Start-MeshCoreBridgeDaemon.ps1`, `scripts/windows/Install-MeshCoreBridgeScheduledTask.ps1`, and `docs/windows-daemon-scheduled-task.md` preserve dry-run/no-open defaults, require `-EnableRealPorts`/`-OpenRealPorts` for live scheduled-task port opening, target `pocket1=COM5` and `pocket2=COM8`, and document `%LOCALAPPDATA%\\MeshCoreBitchatBridge` log/state paths.
- Decision `D020` added: Windows daemon persistence remains explicit live-port gated.
- Verification commands passed:

```text
python3 tools/bridge_sim.py --one-way --alice-text 'smoke test over simulated MeshCore'
# delivered one alice -> bob simulated message

python3 tools/bridge_serial.py --port /dev/ttyUSB0 'serial smoke'
# printed one dry-run serial packet, no port opened

python3 tools/bridge_pump_demo.py
# printed one fake-only bridge pump JSON summary with no-hardware safety markers

python3 tools/no_hardware_smoke.py
# ran the three documented demo CLIs locally and printed a stable no-hardware JSON transcript

python3 -m unittest tests.test_bitchat_packet_fixture -v
# Ran 7 Gate 4A/4B packet fixture tests in 0.001s and passed

python3 -m unittest tests.test_bitchat_identity_fixture -v
# Ran 6 Gate 4C/4D identity/signature/verified-sender tests in 0.007s and passed

python3 -m unittest tests.test_bitchat_v2_route_fragment_fixture -v
# Ran 5 Gate 4E v2/route/fragment tests in 0.001s and passed

python3 -m unittest tests.test_bitchat_app_adapter -v
# Ran 4 Gate 5A app-native adapter seam tests in 0.001s and passed

python3 -m unittest tests.test_bitchat_app_adapter_pump -v
# Ran 4 Gate 5B adapter-backed pump tests in 0.001s and passed

python3 -m unittest discover -s tests -v
Ran 91 tests in 0.548s
OK

python -m pytest -q
91 passed in 0.85s

python -m pytest -q
91 passed in 0.65s

# iOS Gate 5E local checkout verification
xcodebuild not available on this host
exit_code=127

python - <<'PY'
# static balance/shape checks for modified Swift files
PY
static_modified_swift_checks=ok

cd /tmp/bitchat-ios && git status --short --branch && git log -4 --oneline --decorate
## gate5e-ios-adapter-stub
72cb7f4 (HEAD -> gate5e-ios-adapter-stub) Add disabled Mesh bridge config owner
44bb8b0 Make bridge adapter stub parser-compatible
72fdf18 Add debug MeshCore bridge hooks
dfdcd6f Add disabled MeshCore bridge adapter stub

# MacBook Gate 5E verification
ssh ericdecker@erics-macbook-pro-1.tailcc761.ts.net 'xcodebuild -version; swift package describe; xcrun swiftc -parse <modified app files>'
Xcode 13.2.1
Build version 13C100
swift package describe blocked: package uses Swift tools version 5.9.0 but installed version is 5.5.0
xcodebuild -list blocked: didn't find classname for 'isa' key in newer .xcodeproj objects
mac_gate5e_config_parse_shape_checks=ok

python -m pytest -q
91 passed in 0.65s

python -m pytest -q
91 passed in 0.67s

python3 -m unittest discover -s tests -v
Ran 91 tests in 0.577s
OK

python3 -m unittest discover -s tests -v
Ran 91 tests in 0.491s
OK

python3 -m unittest tests.test_ios_debug_adapter_fixture -v
Ran 5 tests in 0.000s
OK

python3 -m unittest discover -s tests -v
Ran 96 tests in 0.533s
OK

python3 -m unittest tests.test_windows_daemon_scripts -v
Ran 3 tests in 0.000s
OK

python3 -m unittest discover -s tests -v
Ran 99 tests in 0.531s
OK

python3 tools/meshcore_bridge_daemon.py --port pocket1=COM5 --port pocket2=COM8 --event-log /tmp/meshcore-daemon-dryrun.jsonl --state-file /tmp/meshcore-daemon-state.json --duration-seconds 1
mode=dry-run-no-ports-opened; event_count=1; delivered_count=0; parse_error_count=0; reconnect_count=0; JSONL daemon_plan written; no ports opened

# Windows desktop Gate 2I scheduled-task smoke over Tailscale SSH
C:\Users\station1\AppData\Local\Programs\Python\Python311\python.exe -m pip install cryptography pyserial
# cryptography 49.0.0 installed; pyserial 3.5 already present

.\scripts\windows\Install-MeshCoreBridgeScheduledTask.ps1 -StartNow
# dry-run scheduled task registered and completed with LastTaskResult=0; latest stdout log reported mode=dry-run-no-ports-opened and event_count=1

.\scripts\windows\Install-MeshCoreBridgeScheduledTask.ps1 -EnableRealPorts -StartNow
# live scheduled task registered and left running; task State=4 (Running), LastTaskResult=267009 (task still running)
# latest JSONL: daemon_plan, port_opened COM5/pocket1, port_opened COM8/pocket2; stderr length=0 after 20-second check

# 60-minute passive live daemon watch from 2026-06-14T22:46:40Z to 2026-06-14T23:47:06Z
# report: .hermes/runtime/meshcore-daemon-watch-20260614T224640Z.jsonl
# samples=13; ssh_fail=1 transient sample; parse_fail=1 same transient sample; task_statuses={'Running': 12}; last_results={'267009': 12}
# stderr_nonzero_samples=0; error_samples_tail50=[]; latest_event_counts_tail50: daemon_plan=1, port_opened=2, port_open_failed=0, serial_read_error=0, parse_error=0
# state file was absent/zero-length during the passive watch because no active message send/state-save event was injected.

# Hermes script-only watchdog/reporting
# ~/.hermes/scripts/meshcore_daemon_watchdog.py prints nothing when healthy; alerts only for repeated SSH failures, non-running task state, unexpected task result, non-empty daemon stderr, or port_open_failed/serial_read_error/parse_error events.
# Hermes cron job f33031865d0a "MeshCore daemon watchdog" runs every 15 minutes and delivers alerts to the origin Telegram chat.

# Active scheduled-task message smoke with explicit transmit approval
# Commit de43f6a added installer -InjectText support for one-shot scheduled-task smoke injections; local full tests passed (99 tests).
# First smoke attempt after stopping the task left an orphaned prior daemon process holding COM5/COM8, causing 46 port_open_failed events and inject_skipped_port_closed. This was recovered by killing stale meshcore_bridge_daemon.py process trees before retrying; persistent daemon was restarted cleanly.
# Commit 974554a fixed daemon/live-smoke polling so unknown/non-channel queued sync-next responses (observed unknown_0x08) trigger another CMD_SYNC_NEXT_MESSAGE poll. Local full tests passed (101 tests).
# Successful scheduled-task smoke: MeshCoreBitchatBridgeSmoke -EnableRealPorts -StartNow -DurationSeconds 60 -InjectText "pocket1:sched-smoke-20260614-2018".
# Smoke log C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-201255.jsonl: port_opened COM5/COM8, injected_text on COM5, log_rx_data+msg_waiting on COM8, delivered channel_data_recv text "sched-smoke-20260614-2012" from previous queued attempt and "sched-smoke-20260614-2018" from current attempt, no parse_error/serial_read_error/port_open_failed, stderr length=0, state saved next_message_id=16931.
# Persistent task restarted after smoke: MeshCoreBitchatBridgeDaemon State=Running, LastTaskResult=267009, latest log C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-201408.jsonl has daemon_plan plus port_opened COM5/COM8 and stderr length=0. Watchdog job f33031865d0a was resumed after a manual healthy check.

# Third Pocket inventory / first integration attempt
# Eric reported the third Pocket already has MeshCore installed and is plugged in. Windows inventory on home-pc-atl2 found it as COM10, VID:PID=239A:8029, serial 559CC86D2A1B111F. Existing devices remain COM5 serial BAE292D6B7431B72 and COM8 serial 99EF9E1DC9D17560.
# Commit 289e85e added optional -Pocket3Port support to the Windows launcher/installer and kept local tests green (101 tests). Commit 3d4b361 fixed scheduled-task injection-array quoting; local tests still pass (101 tests).
# Live stability attempts COM10<->COM5 and COM10<->COM8 each ran 6 alternating attempts with real ports open; both delivered 0/6 and had zero notifications/parse errors. This suggests COM10 is visible/openable but not on the same MeshCore USB Companion RF/config path as COM5/COM8.
# Persistent daemon was restarted with three ports: MeshCoreBitchatBridgeDaemon State=Running, LastTaskResult=267009, latest log C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-202921.jsonl opened COM5/COM8/COM10 and stderr length=0. The latest log also saw an ASCII serial chunk from pocket3: hex 424c453a20777269746542797465733a20737a3d35362c206864723d3133360a = "BLE: writeBytes: sz=56, hdr=136\n", which is not a MeshCore companion-framed notification. Eric clarified COM10 is running the latest MeshCore Bluetooth install and functions via his iPhone, so it is intentionally not a USB Companion endpoint. The persistent daemon was reverted to the two USB Companion ports only: latest log C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-203623.jsonl opened COM5/COM8 only, stderr length=0, State=Running/267009. Keep COM10 free for iPhone/Bluetooth use unless Eric explicitly asks to reconfigure/flash it.
# User asked to make sure COM5 and COM8 are set to the US 915 MHz range. Using CMD_APP_START/SELF_INFO, both were found at 869.618 MHz with BW 62.5 kHz, SF 8, CR 5. Sent CMD_SET_RADIO to both preserving BW/SF/CR and setting freq=915.0 MHz. Verification after write showed COM5 name C8BB12CB and COM8 name D0521521 both at freq=915.0, BW=62.5, SF=8, CR=5. A post-set stability attempt initially saw RF log_rx_data but no delivered channel-data; after reboot commands and 12s wait, 4-message COM5<->COM8 stability delivered 4/4, avg latency ~0.871s, no duplicates, no parse errors. Persistent daemon was restarted; latest log C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-204548.jsonl opened COM5/COM8, stderr length=0, State=Running/267009. Watchdog check passed and cron f33031865d0a resumed.
# Eric then shared COM10/iPhone settings: USA/Canada preset, freq 910.525 MHz, BW 62.5 kHz, SF 7, CR 5, TX power 22, repeat disabled. COM5/COM8 were aligned to those radio params via CMD_SET_RADIO (freq=910.525, BW=62.5, SF=7, CR=5), verified by SELF_INFO, rebooted, and retested. Post-align 4-message COM5<->COM8 stability delivered 4/4, avg latency ~0.652s, no duplicates, no parse errors. Persistent daemon was restarted; latest log C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-205317.jsonl opened COM5/COM8, stderr length=0, State=Running/267009. Watchdog check passed and cron f33031865d0a resumed.
# Eric sent an iPhone/COM10 MeshCore text to both after radio alignment. Latest daemon log C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-205317.jsonl showed RF activity and msg_waiting on both pocket1/COM5 and pocket2/COM8. Sync-next returned unknown_0x07 frames on both containing ASCII "Test from 3" and unknown_0x81 follow-up frames. This proves both USB Companion nodes receive the iPhone node after alignment, but stock MeshCore text payload type 0x07 is not yet decoded by the daemon.
# Commit 1d24403 adds stock MeshCore text decoding: 0x07/0x08/0x10/0x11 classify as contact/channel text frames, emit meshcore_text_message JSONL events with text, pubkey_prefix/channel_idx, timestamp, path metadata, and txt_type; 0x81 classifies as path_update. Local suite passed 104 tests. Windows repo on home-pc-atl2 was reset to origin/main at 1d24403; focused parser tests passed; recorded payload smoke decoded both previous iPhone frames as contact_msg_recv text "Test from 3". Daemon restarted at C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-210412.jsonl, opened COM5/COM8, stderr length=0, State=Running/267009. Watchdog check passed and cron f33031865d0a resumed.
# Eric sent another iPhone/COM10 message after decoder deployment. Live log C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-210412.jsonl produced two meshcore_text_message events: pocket2/COM8 text "Second test from iphone connection " and pocket1/COM5 text "Second test from iphone connection ??". The pocket1 raw payload ends f09f918d (emoji bytes; PowerShell rendered as ??). This confirms live iPhone sends now become readable meshcore_text_message events.
# Commit 5252f10 adds gated stock MeshCore text relay: --relay-stock-text plus --relay-stock-text-prefix default "[relay] ", CMD_SEND_CHANNEL_TXT_MSG command builder, dedupe by scope/pubkey/channel/timestamp/txt_type/text, loop guard for already-prefixed relay text, and JSONL events relay_stock_text_sent / skipped_duplicate / skipped_loop_guard / skipped_empty / skipped_no_targets / relay_stock_text_error. Windows launcher/installer now expose -RelayStockText and -EnableStockTextRelay. Local suite passed 106 tests. Windows repo on home-pc-atl2 reset to 5252f10; four focused relay/script tests passed; command smoke built 030001393000005b72656c61795d20736d6f6b65 for "[relay] smoke". Persistent scheduled task was relay-enabled at C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-211450.jsonl, opened COM5/COM8, stderr length=0, State=Running/267009.
# First live relay smoke exposed a relay loop: stock MeshCore channel messages prepend the device name before "[relay]", so the original startswith loop guard missed them and the daemon repeatedly relayed channel echoes. Daemon was stopped and PID 82228 killed to halt the loop. Commit ef9ba68 fixes this by relaying only unprefixed stock contact messages; channel messages are skipped as relay_stock_text_skipped_non_contact, and contact messages containing the relay prefix are skipped as relay_stock_text_skipped_loop_guard. Local suite passed 107 tests. Windows repo reset to ef9ba68; focused test passed; fixed relay daemon restarted at C:\Users\station1\AppData\Local\MeshCoreBitchatBridge\logs\meshcore-bridge-20260614-212327.jsonl, opened COM5/COM8, stderr length=0, State=Running/267009. Watchdog check passed and cron f33031865d0a resumed.
```

## Approval note

Eric approved continuing local implementation to the project's logical MVP conclusion without asking before each bounded local loop. External/public actions still require separate approval.

## Current milestone

Post-MVP gate map complete, Gate 1 local release hygiene preflight is documented in `docs/public-release-preflight.md`, and the public source repository has been created and pushed at <https://github.com/redclawanon-rgb/meshcore-bitchat-bridge>. Repo settings verified: public visibility, default branch `main`, issues enabled, wiki disabled, discussions disabled, MIT license detected, no release/tag/public announcement created. Gate 2I Windows daemon scheduled-task wrapper is implemented and live-installed on `home-pc-atl2`: dry-run task completed with `LastTaskResult=0`; live task was registered with `-EnableRealPorts -StartNow`, opened `COM5` and `COM8`, remained running with stderr length 0, passed a 60-minute passive watch with no daemon-side errors observed, and passed an active scheduled-task message smoke delivering the approved test text over COM5→COM8 after a polling fix for queued non-channel sync-next responses. Third Pocket has been inventoried as `COM10` / serial `559CC86D2A1B111F`; Eric clarified it is intentionally running latest MeshCore Bluetooth firmware for iPhone use, not USB Companion, so the daemon is back to COM5/COM8 only.

## Next recommended loop / gate

Gate 1 publication is complete for source-only repo creation/push. Gate 2A hardware inventory preflight is recorded in `docs/hardware-inventory-preflight.md`: no candidate `/dev/ttyUSB*`, `/dev/ttyACM*`, or `/dev/serial/...` device was visible on this host/session, `lsusb` is not installed, no real serial/BLE/hardware access was attempted, no-hardware smoke passed, and 59 tests passed. Gate 2B target setup is recorded in `docs/rak4631-target-setup.md` for the loose RAK19003 + RAK4631 assembly. Gates 2C/2D/2E are complete for two MeshCore-flashed WisMesh Pockets on Eric's Windows home desktop: `pocket-1` is `COM5` / serial `BAE292D6B7431B72`; `pocket-2` is `COM8` / serial `99EF9E1DC9D17560`; the 20-message stability loop delivered 20/20 alternating messages with no duplicates or parse errors. Gates 2F/2G/2H are complete for the MeshCore-side daemon: named real-port opening is gated by `--open-real-ports`, JSONL event logging and state persistence are implemented, and live unplug/replug recovery for `pocket2` / `COM8` was proven. Gate 2I Windows scheduled-task wrapper is implemented, dry-run task registration passed, the live scheduled task is installed/running on `home-pc-atl2` with `COM5` and `COM8` opened, a 60-minute passive watch passed with 12/13 successful SSH samples all reporting `Running`, one transient SSH miss, zero stderr, and zero parse/serial/open errors in daemon logs, and an active scheduled-task smoke delivered the approved test message COM5→COM8 with state persistence. Gate 4 scoped bitchat adapter research plus Gate 4A/4B/4C/4D/4E conformance fixtures are complete, Gates 5A/5B app-adapter seam/pump integration are complete, Gate 5C Android/iOS insertion-point mapping is complete, Gate 5D platform-neutral app adapter API spec is complete, and Gate 5E iOS-first disabled/debug stub plus debug inbound/outbound hooks/config owner and bridge-side config fixture simulation are complete. Recommended next gated choices: third Pocket flashing, continue non-Xcode iOS source validation, live BLE/app integration, production/security review, tags/releases, or public announcements.

## Blockers

- Real bitchat-side adapter is not implemented/proven yet.
- Third WisMesh Pocket is still presumed Meshtastic/unknown firmware unless separately checked/flashed.
- Real stock bitchat integration remains unscoped and unclaimed; future work needs version-pinned upstream API/conformance decisions.
