# MeshCore ↔ bitchat Bridge

Experimental MVP project to bridge bitchat-like messages over MeshCore/LoRa.

## MVP target

Two MeshCore-capable nodes exchange custom bridge frames over LoRa, while a minimal client injects and reads text messages through a BLE/serial companion path.

## Non-goals for MVP

- Full stock bitchat app compatibility
- Private DMs
- Full Noise tunnel
- Nostr bridge
- Image/file transfer
- Production security claims

## First milestone

Build a bridge-frame protocol, codec, fragmentation tests, then a MeshCore custom-payload firmware spike.

## Project OS

Future agent/human work should start with:

1. `.hermes/context.md`
2. `STATUS.md`
3. `DECISIONS.md`
4. `LOOPS.md`
5. Current GitHub/local issue or task
