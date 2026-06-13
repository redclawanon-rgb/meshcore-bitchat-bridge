# Status

## Current state

Local-first development is underway. Bridge frame v0 is locked, local codec is implemented, message-level UTF-8 text fragmentation/reassembly helpers are implemented, a local CLI harness can encode/decode frames without hardware, and MeshCore companion channel-data command/notification wrappers are implemented locally.

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
- Verification command passed:

```text
python3 -m unittest discover -s tests -v
Ran 25 tests in 0.006s
OK
```

## Approval note

Eric approved continuing local implementation to the project's logical MVP conclusion without asking before each bounded local loop. External/public actions still require separate approval.

## Current milestone

MVP-08: simulated end-to-end node harness.

## Next recommended loop

Create a no-hardware two-node simulator:

- create `tools/bridge_frame_codec/sim.py`;
- model two nodes with outbound MeshCore companion commands and inbound `RESP_CODE_CHANNEL_DATA_RECV` notifications;
- support sending text A → B and B → A;
- prove:
  - one-frame text roundtrip;
  - multi-frame text roundtrip;
  - duplicate inbound notification is ignored or handled safely;
  - corrupt frame is rejected;
- optionally add `tools/bridge_sim.py` CLI for demo output.

## Blockers

- Hardware availability not confirmed.
- Target boards not chosen.
- GitHub remote not created.
- bitchat transport seam not inspected yet.
