# Status

## Current state

Local-first development is underway. MVP-03 bridge frame v0 is locked and MVP-04 local codec is implemented with unit tests.

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
- Verification command passed:

```text
python3 -m unittest discover -s tests -v
Ran 9 tests in 0.001s
OK
```

## Current milestone

MVP-05: fragmentation/reassembly harness and message-level behavior.

## Next recommended loop

Extend the local codec into a message-level harness:

- create `tools/bridge_frame_codec/message.py` or extend existing module carefully;
- add text helper functions:
  - UTF-8 text → `TEXT_FRAGMENT` frames;
  - frames → UTF-8 text;
- add deterministic message IDs for tests;
- add tests for:
  - empty text;
  - ASCII text;
  - multi-byte UTF-8 split across fragments;
  - message too large for 255 fragments;
  - mixed message IDs rejected.

## Blockers

- Hardware availability not confirmed.
- Target boards not chosen.
- GitHub remote not created.
- bitchat transport seam not inspected yet.
