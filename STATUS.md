# Status

## Current state

Local-first development is underway. Bridge frame v0 is locked, local codec is implemented, message-level UTF-8 text fragmentation/reassembly helpers are implemented, and a local CLI harness can encode/decode frames without hardware.

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
- Verification command passed:

```text
python3 -m unittest discover -s tests -v
Ran 19 tests in 0.005s
OK
```

- CLI smoke test passed:

```text
python3 tools/bridge_cli.py encode-text --bridge-id 0x1 --message-id 0x2 'hello mesh'
python3 tools/bridge_cli.py decode-frames <encoded_hex>
```

Returned decoded text: `hello mesh`.

## Approval note

Eric approved continuing local implementation to the project's logical MVP conclusion without asking before each bounded local loop. External/public actions still require separate approval.

## Current milestone

MVP-07: local MeshCore companion frame wrapper.

## Next recommended loop

Add a local MeshCore companion channel-data wrapper around encoded bridge frames:

- create `tools/bridge_frame_codec/meshcore_companion.py`;
- implement channel datagram send frame builder for command `0x3E`:
  - channel index;
  - path length `0xFF` for flood;
  - `data_type` default `0xFFFF`;
  - bridge payload bytes;
- implement parser for inbound `RESP_CODE_CHANNEL_DATA_RECV` (`0x1B`);
- add tests verifying command bytes and inbound parsing;
- still keep hardware/BLE out of scope.

## Blockers

- Hardware availability not confirmed.
- Target boards not chosen.
- GitHub remote not created.
- bitchat transport seam not inspected yet.
