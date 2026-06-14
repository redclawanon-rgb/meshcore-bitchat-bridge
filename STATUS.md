# Status

## Current state

Local-first development is underway. Bridge frame v0 is locked, local codec is implemented, message-level UTF-8 text fragmentation/reassembly helpers are implemented, a local CLI harness can encode/decode frames without hardware, MeshCore companion channel-data command/notification wrappers are implemented locally, a no-hardware two-node simulator proves end-to-end text exchange over the local stack, and a simulator demo CLI prints deterministic A ↔ B exchange summaries.

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
- Verification commands passed:

```text
python3 tools/bridge_sim.py --one-way --alice-text 'smoke test over simulated MeshCore'
# delivered one alice -> bob simulated message

python3 -m unittest discover -s tests -v
Ran 33 tests in 0.011s
OK
```

## Approval note

Eric approved continuing local implementation to the project's logical MVP conclusion without asking before each bounded local loop. External/public actions still require separate approval.

## Current milestone

MVP-10 complete: serial/BLE/hardware adapter path decision documented.

## Next recommended loop

MVP-11: transport interface + fake transport harness:

- create `tools/bridge_frame_codec/transport.py`;
- create `tests/test_bridge_transport.py`;
- define an async-ish or simple testable interface around companion command/notification bytes;
- prove send/receive through fake transport using existing simulator byte path;
- keep real hardware access gated.

## Blockers

- Hardware availability not confirmed.
- Target boards not chosen.
- GitHub remote not created.
- bitchat transport seam not inspected yet.
