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

## No-hardware demo CLIs

These demos are local sanity checks for the bridge-frame, MeshCore companion
datagram, and text-only carrier seams. They are safe to run on a development
machine without radios attached.

### Two-node MeshCore simulator

```bash
python3 tools/bridge_sim.py --one-way --alice-text 'smoke test over simulated MeshCore'
```

What it does:

- Builds bridge-frame text command(s) from a simulated Alice node.
- Converts them into simulated MeshCore channel-data notifications.
- Delivers them into a simulated Bob node.
- Prints JSON with `mode: "no-hardware"`, command/notification counts, delivered text, and inbox summaries.

### Serial packet dry run

```bash
python3 tools/bridge_serial.py --port /dev/ttyUSB0 'serial smoke'
```

What it does:

- Encodes the text into MeshCore companion channel-data command bytes.
- Wraps those commands as serial TX packet bytes.
- Prints JSON with `mode: "dry-run-no-port-opened"`, packet lengths, `serial_tx_hex`, and `companion_command_hex`.
- Shows the requested `--port` and `--baud` for operator context only.

By default this command does **not** open `/dev/ttyUSB0` or any other serial
port. Real serial writes are gated behind the explicit `--open-real-port` flag
and are outside the no-hardware demo path.

### Fake bridge pump demo

```bash
python3 tools/bridge_pump_demo.py
```

What it does:

- Wires a fake MeshCore companion transport, simulated MeshCore nodes, and a fake semantic bitchat text carrier.
- Pumps one MeshCore-delivered text into the fake carrier.
- Pumps one fake carrier-originated public text back through the MeshCore transport-neutral path.
- Prints JSON with `mode: "no-hardware"`, explicit safety markers, pump counts, carrier publications, receiver inbox, and fake transport summaries.

### Drift-resistant no-hardware smoke transcript

```bash
python3 tools/no_hardware_smoke.py
```

What it does:

- Runs the three documented demo CLIs above as local subprocesses.
- Parses each CLI's JSON output and emits one stable JSON transcript with selected fields.
- Keeps README/demo examples checkable without opening serial, BLE, hardware, network, secrets, or stock bitchat integration.
- Invokes `bridge_serial.py` only in its default `dry-run-no-port-opened` path.

### Safety and compatibility boundaries

- No serial port is opened by default.
- No BLE adapter is opened or scanned by these demos.
- `bridge_sim.py`, `bridge_pump_demo.py`, and `no_hardware_smoke.py` use local subprocesses plus simulated/fake transports only.
- `bridge_serial.py` is a dry-run byte encoder unless `--open-real-port` is explicitly provided.
- The bitchat-side MVP seam is semantic public text only; these demos do not forge stock `BitchatPacket` bytes.
- No stock bitchat app compatibility, interoperability, privacy, or production-security claims are made by these demos.

## Project OS

Future agent/human work should start with:

1. `.hermes/context.md`
2. `STATUS.md`
3. `DECISIONS.md`
4. `LOOPS.md`
5. Current GitHub/local issue or task
