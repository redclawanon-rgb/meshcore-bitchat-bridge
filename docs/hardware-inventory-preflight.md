# Hardware inventory preflight

Date: 2026-06-14

This records Gate 2A hardware inventory / target selection preflight. It does not open serial ports, scan BLE, flash hardware, purchase hardware, or run any real-port command.

## Commands run

From the project root:

```bash
git status --short --branch
python3 tools/no_hardware_smoke.py
python3 -m unittest discover -s tests -v
```

Candidate serial device inspection was performed by listing common device paths only:

- `/dev/ttyUSB*`
- `/dev/ttyACM*`
- `/dev/serial/by-id/*`
- `/dev/serial/by-path/*`

This does not open the device files.

## Result

- Git state before inventory: `## main...origin/main`
- Candidate serial devices: none found
- `/dev/ttyUSB*`: none found
- `/dev/ttyACM*`: none found
- `/dev/serial/by-id/*`: none found
- `/dev/serial/by-path/*`: none found
- `lsusb`: not installed in this environment
- Current user groups: `openclaw`, `sudo`, `users`, `docker`
- `dialout` group exists, but current user is not a member in this shell
- No-hardware smoke result:
  - `type`: `meshcore_bitchat_bridge_no_hardware_smoke_v0`
  - `mode`: `no-hardware`
  - `demo_count`: `3`
  - safety markers: no serial, no BLE, no network, no real hardware, stock compatibility not claimed
- Full tests: `59` tests passed

## Readiness interpretation

Gate 2A did not identify a connected MeshCore-capable serial device on this host/session. Gate 2B/Gate 2C should not proceed until a target board and port are identified.

To continue the hardware path, identify or connect a MeshCore-capable board and record:

- Board/model
- Firmware/source/version/commit
- Host machine where it is connected
- Serial port path, preferably stable `/dev/serial/by-id/...` if available
- Baud rate, expected default `115200` unless confirmed otherwise
- Whether real serial access is authorized for that exact device/port

## Stop point

Stopped before any real serial/BLE/hardware access. No `--open-real-port` command was run.
