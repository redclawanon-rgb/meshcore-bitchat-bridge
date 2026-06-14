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

python3 -m unittest discover -s tests -v
Ran 59 tests in 0.304s
OK
```

## Approval note

Eric approved continuing local implementation to the project's logical MVP conclusion without asking before each bounded local loop. External/public actions still require separate approval.

## Current milestone

Post-MVP gate map complete, Gate 1 local release hygiene preflight is documented in `docs/public-release-preflight.md`, and the public source repository has been created and pushed at <https://github.com/redclawanon-rgb/meshcore-bitchat-bridge>. Repo settings verified: public visibility, default branch `main`, issues enabled, wiki disabled, discussions disabled, MIT license detected, no release/tag/public announcement created.

## Next recommended loop / gate

Gate 1 publication is complete for source-only repo creation/push. Gate 2A hardware inventory preflight is recorded in `docs/hardware-inventory-preflight.md`: no candidate `/dev/ttyUSB*`, `/dev/ttyACM*`, or `/dev/serial/...` device was visible on this host/session, `lsusb` is not installed, no real serial/BLE/hardware access was attempted, no-hardware smoke passed, and 59 tests passed. Gate 2B target setup is recorded in `docs/rak4631-target-setup.md` for the loose RAK19003 + RAK4631 assembly. Gate 2C first live serial smoke and Gate 2D actual bidirectional over-LoRa delivery are complete for two RAKwireless WisMesh Pockets on Eric's Windows home desktop: `pocket-1` is `COM5` / serial `BAE292D6B7431B72`; `pocket-2` is `COM8` / serial `99EF9E1DC9D17560`; both are flashed to MeshCore USB Companion. Gate 2E short stability loop is complete: `tools/live_lora_stability.py --port-a COM5 --port-b COM8 --count 20 --listen-seconds 8 --pause-seconds 0.25 --open-real-ports` delivered 20/20 alternating messages, delivery_rate `1.0`, failed `0`, duplicate_deliveries `0`, parse_error_count `0`, and latency seconds min/avg/median/max ≈ `0.859/0.875/0.875/0.891`. Remaining gated choices: build a continuous bridge daemon, run a longer/range/interference loop, flash/use the third Pocket, BLE exploration, scoped stock bitchat compatibility research, or production/security review last. Tags/releases/public announcements are still not created unless separately requested.

## Blockers

- Gate 2E short bidirectional stability loop is complete for `pocket-1` and `pocket-2`; long-duration daemon behavior, range/interference performance, and recovery from serial/device disconnects are not implemented/proven yet.
- Third WisMesh Pocket is still presumed Meshtastic/unknown firmware unless separately checked/flashed.
- Real stock bitchat integration remains unscoped and unclaimed; future work needs version-pinned upstream API/conformance decisions.
