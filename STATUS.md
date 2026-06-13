# Status

## Current state

Local-first development is underway. Bridge frame v0 is locked, local codec is implemented, and message-level UTF-8 text fragmentation/reassembly helpers are implemented.

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
- Verification command passed:

```text
python3 -m unittest discover -s tests -v
Ran 16 tests in 0.002s
OK
```

## Current milestone

MVP-06: local bridge harness CLI.

## Next recommended loop

Create a local CLI that can encode/decode text frames without hardware:

- create `tools/bridge_cli.py`;
- commands:
  - `encode-text --bridge-id HEX_OR_INT --message-id HEX_OR_INT TEXT` → JSON frames with hex payloads;
  - `decode-frames FRAME_HEX...` → reassembled text;
- add tests or documented smoke commands;
- keep hardware and BLE out of scope for this loop.

## Blockers

- Hardware availability not confirmed.
- Target boards not chosen.
- GitHub remote not created.
- bitchat transport seam not inspected yet.
