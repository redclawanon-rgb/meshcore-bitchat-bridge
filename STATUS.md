# Status

## Current state

Local-first development is underway. Bridge frame v0 is locked, local codec is implemented, message-level UTF-8 text fragmentation/reassembly helpers are implemented, a local CLI harness can encode/decode frames without hardware, MeshCore companion channel-data command/notification wrappers are implemented locally, a no-hardware two-node simulator proves end-to-end text exchange over the local stack, a simulator demo CLI prints deterministic A ↔ B exchange summaries, a transport-neutral companion datagram seam has a fake transport harness, a no-hardware serial adapter scaffold/dry-run CLI emits exact MeshCore serial packet bytes, the serial companion datagram transport is exercised through the transport-neutral bridge path with fake streams only, a no-hardware orchestration smoke replays serial dry-run TX packet bytes through the simulator/fake-stream receiver path, the bitchat-side public-text seam has been inspected/designed as a semantic text-only carrier boundary without stock compatibility claims, and a fake in-memory `BitchatTextCarrier` now proves decoded bridge text handoff plus carrier-originated text forwarding through the existing MeshCore transport-neutral path.

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
- Verification commands passed:

```text
python3 tools/bridge_sim.py --one-way --alice-text 'smoke test over simulated MeshCore'
# delivered one alice -> bob simulated message

python3 tools/bridge_serial.py --port /dev/ttyUSB0 'serial smoke'
# printed one dry-run serial packet, no port opened

python3 -m unittest discover -s tests -v
Ran 51 tests in 0.013s
OK
```

## Approval note

Eric approved continuing local implementation to the project's logical MVP conclusion without asking before each bounded local loop. External/public actions still require separate approval.

## Current milestone

MVP-17 complete: implemented the local fake bitchat-side semantic text carrier seam and tests. `FakeBitchatTextCarrier` records decoded bridge text and queues fake carrier-originated public text without BLE, stock packet forging, hardware, or compatibility claims.

## Next recommended loop

MVP-18: add a tiny local bridge orchestration helper that drains MeshCore-delivered `DeliveredText` into a `BitchatTextCarrier` and forwards carrier-originated public text into the MeshCore transport-neutral path in one no-hardware pump function, with fake-only tests.

## Blockers

- Hardware availability not confirmed.
- Target boards not chosen.
- GitHub remote not created.
- Real stock bitchat integration remains unscoped and unclaimed; future work needs version-pinned upstream API/conformance decisions.
