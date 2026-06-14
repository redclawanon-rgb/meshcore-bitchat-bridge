# Status

## Current state

Local-first development is underway. Bridge frame v0 is locked, local codec is implemented, message-level UTF-8 text fragmentation/reassembly helpers are implemented, a local CLI harness can encode/decode frames without hardware, MeshCore companion channel-data command/notification wrappers are implemented locally, a no-hardware two-node simulator proves end-to-end text exchange over the local stack, a simulator demo CLI prints deterministic A ↔ B exchange summaries, a transport-neutral companion datagram seam has a fake transport harness, a no-hardware serial adapter scaffold/dry-run CLI emits exact MeshCore serial packet bytes, and the serial companion datagram transport is exercised through the transport-neutral bridge path with fake streams only.

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
- Gated hardware smoke checklist drafted at `HARDWARE_SMOKE.md`; real serial access remains behind explicit Eric invocation and `--open-real-port`/`open_real_port=True`.
- Verification commands passed:

```text
python3 tools/bridge_sim.py --one-way --alice-text 'smoke test over simulated MeshCore'
# delivered one alice -> bob simulated message

python3 tools/bridge_serial.py --port /dev/ttyUSB0 'serial smoke'
# printed one dry-run serial packet, no port opened

python3 -m unittest discover -s tests -v
Ran 46 tests in 0.013s
OK
```

## Approval note

Eric approved continuing local implementation to the project's logical MVP conclusion without asking before each bounded local loop. External/public actions still require separate approval.

## Current milestone

MVP-14 complete: serial companion datagram transport exercised through the transport-neutral bridge path with fake streams, and gated hardware smoke checklist drafted.

## Next recommended loop

MVP-15: add a no-hardware bridge orchestration smoke that ties the serial dry-run packet output to the simulator/fake-stream path, keeping real serial access gated.

## Blockers

- Hardware availability not confirmed.
- Target boards not chosen.
- GitHub remote not created.
- bitchat transport seam not inspected yet.
