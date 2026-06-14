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
Ran 59 tests in 0.351s
OK
```

## Approval note

Eric approved continuing local implementation to the project's logical MVP conclusion without asking before each bounded local loop. External/public actions still require separate approval.

## Current milestone

MVP-24 complete: `docs/mvp-handoff-index.md` now provides a local MVP handoff/release-readiness index for a future human operator, cross-linking the protocol, adapter decisions, no-hardware demos, smoke regression fixture/note, pre-hardware readiness, gated hardware checklist, current blockers, and non-claims. The boundary remains local-only: no serial/BLE/hardware/network/secrets/stock bitchat integration, and no cron/nudge/autoloop behavior.

## Next recommended loop / gate

Natural local-docs/code conclusion reached for the current no-hardware MVP handoff. The next step is a real gate, not another autonomous local loop: stop unless Eric explicitly approves one of the gated paths such as public push/post, hardware purchase/flashing/use, real serial/BLE access, secrets handling, production/security claims, or scoped stock bitchat compatibility work.

## Blockers

- Hardware availability not confirmed.
- Target boards not chosen.
- GitHub remote not created.
- Real stock bitchat integration remains unscoped and unclaimed; future work needs version-pinned upstream API/conformance decisions.
