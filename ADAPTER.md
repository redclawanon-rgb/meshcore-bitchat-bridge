# Adapter Path Decision — MVP-10

## Purpose

Define the first live-transport seam after the local simulator. The simulator already proves this byte path:

```text
bridge text
→ bridge frames
→ MeshCore companion channel-data command bytes
→ MeshCore channel-data receive notification bytes
→ bridge frame decode/reassembly
→ delivered text
```

The live adapter should preserve that exact seam. Hardware/BLE/serial code should only replace the in-memory `SimulatedMeshCoreLink`, not rewrite the bridge protocol.

## Sources inspected

- MeshCore `docs/companion_protocol.md` from GitHub `main`, fetched 2026-06-14.
- MeshCore official Python library `meshcore-dev/meshcore_py` README and source tree, fetched 2026-06-14.
- Local bridge implementation:
  - `tools/bridge_frame_codec/meshcore_companion.py`
  - `tools/bridge_frame_codec/sim.py`
  - `tools/bridge_sim.py`

## Relevant upstream facts

### BLE companion path

MeshCore companion docs describe BLE as the companion protocol path.

BLE UUIDs:

- Service: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- RX characteristic, app → firmware: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`
- TX characteristic, firmware → app: `6E400003-B5A3-F393-E0A9-E50E24DCCA9E`

Connection sequence:

1. connect;
2. discover services/characteristics;
3. enable notifications;
4. send initial commands;
5. send one command at a time and wait for responses where required.

MTU note: default BLE payload is small; request/negotiate larger MTU where possible. Python bleak handles MTU negotiation automatically according to the upstream docs.

### Channel data datagram path

The companion docs define channel data datagrams:

```text
Byte 0:                       0x3E
Byte 1:                       Channel Index, 0-7
Byte 2:                       Path Length, 0xFF = flood
Bytes 3..2+path_len:          Path if not flood
Next 2 bytes little-endian:   data_type uint16
Remaining bytes:              binary payload
```

This matches the local helper `build_channel_data_command()`.

Inbound `RESP_CODE_CHANNEL_DATA_RECV` notifications are already modeled locally by `parse_channel_data_recv()` and `SimulatedMeshCoreLink.command_to_notification()`.

### Existing Python library

`meshcore_py` supports:

```python
MeshCore.create_serial("/dev/ttyUSB0", 115200, debug=True)
MeshCore.create_ble("12:34:56:78:90:AB")
MeshCore.create_tcp("192.168.1.100", 4000)
```

Its serial connection wraps outgoing companion bytes as:

```text
0x3c + uint16_le(size) + data
```

Its BLE connection writes bytes to the RX characteristic and subscribes to TX notifications.

The README documents normal message APIs, but the channel-data datagram helper is not clearly exposed in the inspected snippets. Treat raw companion byte send/receive as the stable adapter seam until the library exposes or we add a thin method for command `0x3E`.

## Decision

### First live adapter target: serial-first, BLE-second

Use a transport-neutral adapter interface, but implement serial first when hardware is available.

Rationale:

- Serial is easiest to test from this Linux VPS or a local machine with USB access.
- It avoids BLE scan/pairing/MTU/platform issues during first hardware bring-up.
- `meshcore_py` already documents `create_serial("/dev/ttyUSB0", 115200)` and its serial framing is visible.
- BLE remains the likely mobile/bitchat-adjacent path later, but it adds platform-specific connection handling that should not be mixed into first hardware proof.

BLE should be the second live adapter because stock/mobile bitchat integration will eventually care about mobile transports and BLE lifecycle constraints.

## Adapter interface

Create a small interface around companion bytes:

```python
class CompanionDatagramTransport:
    async def connect(self) -> None: ...
    async def send_channel_data_command(self, command: bytes) -> None: ...
    async def recv_channel_data_notification(self) -> bytes: ...
    async def disconnect(self) -> None: ...
```

Bridge-level code should call:

```python
commands = node.make_text_commands(text)
for command in commands:
    await transport.send_channel_data_command(command)

raw_notification = await transport.recv_channel_data_notification()
node.receive_notification(raw_notification)
```

The simulator is the reference implementation of this interface:

- `SimulatedBridgeNode.make_text_commands()` produces command bytes.
- `SimulatedMeshCoreLink.command_to_notification()` produces notification bytes.
- `SimulatedBridgeNode.receive_notification()` consumes notification bytes.

## Proposed next implementation loop: MVP-11

Add a transport interface and fake transport test harness without talking to hardware yet.

Files:

- `tools/bridge_frame_codec/transport.py`
- `tests/test_bridge_transport.py`

Acceptance checks:

- fake transport accepts exact command bytes from `SimulatedBridgeNode`;
- fake transport emits exact notification bytes;
- bridge send/receive code works against the transport interface instead of directly using `SimulatedMeshCoreLink`;
- full tests still pass.

## Hardware-gated loop after MVP-11

MVP-12 should be serial adapter scaffold, still safe without requiring a board:

- implement serial frame wrapper/unwrapper for `0x3c + uint16_le(size) + command`;
- do not open a real serial port in tests;
- add a dry-run CLI that prints the exact bytes that would be written to `/dev/ttyUSB0`;
- gate real serial open/send until Eric confirms hardware and port.

## Boundaries

- No hardware purchases without Eric approval.
- No public repo push/post without Eric approval.
- No claim that this is stock bitchat-compatible yet.
- No production security claims; current bridge remains lab-only/plaintext framing.
