# Status

## Current state

Project scaffold created. MVP-02 MeshCore packet budget evidence completed.

## Verified

- Local git repo initialized.
- Project OS files created.
- MeshCore docs inspected from GitHub `main`:
  - `docs/packet_format.md`
  - `docs/payloads.md`
  - `docs/companion_protocol.md`
- Evidence written to `evidence/meshcore-payload-budget.md`.

## Current milestone

MVP-03: lock bridge frame v0 protocol around MeshCore companion channel data budget.

## Next recommended loop

Update `PROTOCOL.md` using the evidence:

- carrier: companion channel data datagram / radio `PAYLOAD_TYPE_GRP_DATA`, command `0x3E`
- development data type: `0xFFFF`
- max companion binary payload: 163 bytes
- bridge frame overhead: 23 bytes
- max fragment body: 140 bytes

Then create initial test vector in `tests/vectors/bridge-frame-v0.json`.

## Blockers

- Hardware availability not confirmed.
- Target boards not chosen.
- GitHub remote not created.
- bitchat transport seam not inspected yet.
