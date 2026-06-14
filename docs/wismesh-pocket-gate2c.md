# WisMesh Pocket Gate 2C target

Date: 2026-06-14

This records the Gate 2C target change from the loose RAK19003 + RAK4631 assembly to Eric's three RAKwireless WisMesh Pocket devices. This is intended to make live smoke testing easier because the Pocket units are assembled devices.

No serial port was opened while creating this note. No BLE scan was run. No firmware was flashed.

## Target hardware

Eric has three RAKwireless WisMesh Pocket units.

Treat them as the preferred Gate 2C hardware target before using the separate RAK19003 + RAK4631 assembly.

## MeshCore flasher target evidence

Public upstream evidence was gathered from `meshcore-dev/flasher.meshcore.io` and `meshcore-dev/MeshCore` via GitHub CLI / raw HTTP.

The MeshCore flasher config contains a RAK target named:

```text
RAK WisBlock / WisMesh (RAK 4631)
```

Observed properties:

- maker: `rak`
- type: `nrf52`
- bootloader: `wiscore_rak4631_board_bootloader-0.9.2-OTAFIX2.1.uf2`
- firmware roles:
  - `companionBle`
  - `companionUsb`
  - `repeater`
  - `roomServer`

For this project's serial-first bridge seam, use the **Companion USB** firmware path first.

The latest observed MeshCore companion release remains:

```text
Companion Firmware v1.16.0
Tag: companion-v1.16.0
```

Observed RAK4631 companion assets:

```text
RAK_4631_companion_radio_usb-v1.16.0-07a3ca9.uf2
RAK_4631_companion_radio_usb-v1.16.0-07a3ca9.zip
RAK_4631_companion_radio_ble-v1.16.0-07a3ca9.uf2
RAK_4631_companion_radio_ble-v1.16.0-07a3ca9.zip
```

## Local inventory result

A no-open inventory was rerun after selecting WisMesh Pocket as the preferred target.

Checked without opening serial devices:

- `/dev/ttyUSB*`
- `/dev/ttyACM*`
- `/dev/serial/by-id/*`
- `/dev/serial/by-path/*`

Result:

```text
NO_CANDIDATE_SERIAL_DEVICES_FOUND
```

Other host notes:

- `lsusb` is not installed in this VPS/session.
- Current user groups: `openclaw`, `sudo`, `users`, `docker`.
- `dialout` group exists, but this shell user is not currently a member.

## Verification run

No-hardware smoke summary:

```text
type meshcore_bitchat_bridge_no_hardware_smoke_v0
mode no-hardware
demo_count 3
safety opens_serial=False opens_ble=False opens_network=False uses_real_hardware=False stock_bitchat_compatibility=not-claimed
```

Full tests:

```text
python3 -m unittest discover -s tests -v
Ran 59 tests in 0.328s
OK
```

## Gate 2C live-smoke sequence

Use only one Pocket first. Keep the other two untouched until the first unit is understood.

1. Pick one WisMesh Pocket and label it `pocket-1`.
2. Connect it to the target host with a known-good USB data cable.
3. Re-run no-open inventory and record the exact path:
   - Prefer `/dev/serial/by-id/...` if present.
   - Otherwise use `/dev/ttyACM0` or `/dev/ttyUSB0` only if clearly associated with the device.
4. Confirm installed firmware role if possible:
   - If already MeshCore USB Companion: proceed toward dry-run/guarded smoke.
   - If BLE Companion: good for later BLE gate, but not first serial smoke.
   - If Meshtastic or unknown: flashing MeshCore USB Companion is a separate explicit firmware action.
5. Run the project dry-run command using the chosen port string, without opening the port:

```bash
python3 tools/bridge_serial.py --port <identified-port> 'wismesh pocket serial smoke'
```

6. Only after Eric approves the exact port and command, run the guarded real-port smoke:

```bash
python3 tools/bridge_serial.py --port <identified-port> --open-real-port 'wismesh pocket serial smoke'
```

## Stop criteria

Stop before real serial access if:

- no exact port is visible;
- multiple ports are ambiguous;
- firmware role is unknown and the smoke would depend on USB Companion behavior;
- the user is not in a required serial-access group on the host;
- the command would require flashing firmware without explicit approval;
- the action would use BLE, LoRa transmit behavior, or production/security claims outside the current gate.

## Current stop point

The preferred hardware target is now the three WisMesh Pocket units, but none are visible as serial devices in this VPS/session. Gate 2C remains blocked until one Pocket is connected to the target host and its exact serial path/firmware role are identified.
