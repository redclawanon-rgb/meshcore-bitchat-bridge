# Status

## Current state

Local-first development is underway. Bridge frame v0 is locked, local codec is implemented, message-level UTF-8 text fragmentation/reassembly helpers are implemented, a local CLI harness can encode/decode frames without hardware, MeshCore companion channel-data command/notification wrappers are implemented locally, and a no-hardware two-node simulator now proves end-to-end text exchange over the local stack.

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
- Simulator tests implemented at `tests/test_bridge_sim.py`.
- Verification command passed:

```text
python3 -m unittest discover -s tests -v
Ran 31 tests in 0.007s
OK
```

## Approval note

Eric approved continuing local implementation to the project's logical MVP conclusion without asking before each bounded local loop. External/public actions still require separate approval.

## Current milestone

MVP-08 complete: simulated end-to-end node harness.

## Next recommended loop

MVP-09: add a small demo CLI for the simulator:

- create `tools/bridge_sim.py`;
- allow A → B, B → A, and long-message demo runs;
- print frame/command counts and delivered text summaries;
- keep it no-hardware and deterministic;
- verify with CLI tests or a smoke command.

After that, continue toward MVP-10: serial/BLE/hardware path decision and adapter seam design.

## Blockers

- Hardware availability not confirmed.
- Target boards not chosen.
- GitHub remote not created.
- bitchat transport seam not inspected yet.
