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
- Gate 5E iOS-first disabled/debug app adapter stub added in local iOS checkout `/tmp/bitchat-ios` on branch `gate5e-ios-adapter-stub`, commit `dfdcd6f`; bridge record added at `docs/ios-app-adapter-stub-gate5e.md`; Decision `D016` added. The iOS stub is not wired into BLEService and defaults disabled/no-op.
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
# static balance/shape checks for new Swift files
PY
static_new_swift_checks=ok

cd /tmp/bitchat-ios && git status --short --branch && git log -1 --oneline --decorate
## gate5e-ios-adapter-stub
dfdcd6f (HEAD -> gate5e-ios-adapter-stub) Add disabled MeshCore bridge adapter stub

python -m pytest -q
91 passed in 0.65s
```

## Approval note

Eric approved continuing local implementation to the project's logical MVP conclusion without asking before each bounded local loop. External/public actions still require separate approval.

## Current milestone

Post-MVP gate map complete, Gate 1 local release hygiene preflight is documented in `docs/public-release-preflight.md`, and the public source repository has been created and pushed at <https://github.com/redclawanon-rgb/meshcore-bitchat-bridge>. Repo settings verified: public visibility, default branch `main`, issues enabled, wiki disabled, discussions disabled, MIT license detected, no release/tag/public announcement created.

## Next recommended loop / gate

Gate 1 publication is complete for source-only repo creation/push. Gate 2A hardware inventory preflight is recorded in `docs/hardware-inventory-preflight.md`: no candidate `/dev/ttyUSB*`, `/dev/ttyACM*`, or `/dev/serial/...` device was visible on this host/session, `lsusb` is not installed, no real serial/BLE/hardware access was attempted, no-hardware smoke passed, and 59 tests passed. Gate 2B target setup is recorded in `docs/rak4631-target-setup.md` for the loose RAK19003 + RAK4631 assembly. Gates 2C/2D/2E are complete for two MeshCore-flashed WisMesh Pockets on Eric's Windows home desktop: `pocket-1` is `COM5` / serial `BAE292D6B7431B72`; `pocket-2` is `COM8` / serial `99EF9E1DC9D17560`; the 20-message stability loop delivered 20/20 alternating messages with no duplicates or parse errors. Gates 2F/2G/2H are complete for the MeshCore-side daemon: named real-port opening is gated by `--open-real-ports`, JSONL event logging and state persistence are implemented, and live unplug/replug recovery for `pocket2` / `COM8` was proven. Gate 4 scoped bitchat adapter research plus Gate 4A/4B/4C/4D/4E conformance fixtures are complete, Gates 5A/5B app-adapter seam/pump integration are complete, Gate 5C Android/iOS insertion-point mapping is complete, Gate 5D platform-neutral app adapter API spec is complete, and Gate 5E iOS-first disabled/debug stub is complete in the local iOS checkout. Recommended next gated choices: run iOS tests on macOS/Xcode, add a debug-only iOS inbound hook, add a debug-only iOS outbound wrapper, Windows service/scheduled-task wrapper, longer unattended daemon runtime, third Pocket flashing, live BLE/app integration, production/security review, tags/releases, or public announcements.

## Blockers

- Gate 2H daemon state/log/reconnect hardening is complete and live-smoked; longer unattended runtime, Windows service/scheduled-task wrapper, and real bitchat-side adapter are not implemented/proven yet.
- Third WisMesh Pocket is still presumed Meshtastic/unknown firmware unless separately checked/flashed.
- Real stock bitchat integration remains unscoped and unclaimed; future work needs version-pinned upstream API/conformance decisions.
