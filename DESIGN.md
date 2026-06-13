# Design

## Strategy

Build the bridge in layers:

1. Project OS and evidence docs
2. Bridge frame v0 protocol
3. Deterministic codec and fragmentation harness
4. MeshCore raw/custom payload tunnel
5. Python bridge harness
6. Later: bitchat transport integration

## Architecture sketch

```text
bitchat-like client or harness
  ↓
bridge frame codec + fragmentation
  ↓
MeshCore companion BLE/serial command
  ↓
MeshCore firmware custom/group payload
  ↓
LoRa MeshCore network
  ↓
remote MeshCore node
  ↓
remote bridge client
```

## Key constraints

- MeshCore packets have a small payload budget, so fragmentation is mandatory.
- LoRa latency and airtime limits make rich chat/file transfer unsuitable for MVP.
- MVP security must be labeled lab-only unless encrypted tunneling is implemented.
