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

The preferred hardware target is now the three WisMesh Pocket units. Eric connected one Pocket to the Windows home desktop and reported it appears as `COM5`: `USB Serial Device (COM5)` with PNP ID prefix `USB\\VID_239A&PID_8029`, matching the RAK4631/nRF52840 USB identity observed in MeshCore upstream. `COM3` is Intel AMT SOL and should not be used; `COM4` is CH340 and is probably unrelated unless Eric identifies another attached serial board.

Gate 2C can continue from the Windows desktop using `COM5`. The dry-run/no-open command has succeeded over SSH using Python 3.11 installed at `C:\\Users\\station1\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`:

```powershell
python tools/bridge_serial.py --port COM5 'wismesh pocket serial smoke'
```

Verified dry-run output included:

- `mode`: `dry-run-no-port-opened`
- `port`: `COM5`
- `baud`: `115200`
- `packet_count`: `1`
- `text_bytes`: `27`
- `serial_len`: `57`

The repo is cloned on the Windows desktop at `C:\\Users\\station1\\meshcore-bitchat-bridge` and was up to date at `main...origin/main` when the dry-run passed.

Eric approved flashing `pocket-1` on `COM5` to MeshCore USB Companion.

Firmware and tooling used on the Windows desktop:

- Firmware package: `firmware/RAK_4631_companion_radio_usb-v1.16.0-07a3ca9.zip`
- Source URL: `https://github.com/meshcore-dev/MeshCore/releases/download/companion-v1.16.0/RAK_4631_companion_radio_usb-v1.16.0-07a3ca9.zip`
- SHA-256: `51AEE6E567A8F8E7C1FAE21713ACB3E3283E460675E7BE583D9A2212294D83F5`
- DFU tool: `adafruit-nrfutil 0.5.3.post16`
- Python: `C:\\Users\\station1\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`

Initial serial DFU with `--touch 1200` moved the device from application `COM5` (`VID_239A:PID_8029`) into bootloader `COM6` (`VID_239A:PID_002A`) with the same serial `BAE292D6B7431B72`. The flash then succeeded on `COM6`:

```powershell
python -m nordicsemi.__main__ dfu serial --package firmware/RAK_4631_companion_radio_usb-v1.16.0-07a3ca9.zip -p COM6 -b 115200 --singlebank
```

DFU result:

```text
Activating new firmware
Device programmed.
FLASH_EXIT=0
```

After reboot, the device returned to:

```text
COM5 USB Serial Device VID_239A:PID_8029 SER=BAE292D6B7431B72
```

Post-flash read-only sample at 115200 opened `COM5` and read `0` bytes in 2 seconds, i.e. the earlier Meshtastic debug chatter was gone.

The approved real-port smoke then succeeded:

```powershell
python tools/bridge_serial.py --port COM5 --open-real-port 'wismesh pocket serial smoke'
```

Verified real-port output included:

- `mode`: `real-port-opened`
- `port`: `COM5`
- `baud`: `115200`
- `packet_count`: `1`
- `text_bytes`: `27`
- `serial_len`: `57`

This proves the Windows desktop opened `COM5` and wrote the encoded MeshCore companion packet. It does not yet prove over-LoRa delivery to another MeshCore node.

Eric then plugged in the second WisMesh Pocket and reconnected the first. Both were mapped by stable USB serial:

- `pocket-1`: `COM5`, `VID_239A:PID_8029`, serial `BAE292D6B7431B72`.
- `pocket-2`: `COM8`, `VID_239A:PID_8029`, serial `99EF9E1DC9D17560`.

Eric approved flashing `pocket-2` to MeshCore USB Companion. The same firmware package was used. Touching `COM8` at 1200 baud moved `pocket-2` into bootloader mode as `COM9`, `VID_239A:PID_002A`, serial `99EF9E1DC9D17560`. Flashing succeeded on `COM9`:

```powershell
python -m nordicsemi.__main__ dfu serial --package firmware/RAK_4631_companion_radio_usb-v1.16.0-07a3ca9.zip -p COM9 -b 115200 --singlebank
```

DFU result:

```text
Activating new firmware
Device programmed.
FLASH_EXIT=0
```

After reboot, both MeshCore-flashed Pockets were present:

```text
COM5 USB Serial Device VID_239A:PID_8029 SER=BAE292D6B7431B72
COM8 USB Serial Device VID_239A:PID_8029 SER=99EF9E1DC9D17560
```

Post-flash read-only samples at 115200 opened both ports and read `0` bytes, i.e. no Meshtastic debug chatter from either unit.

Real-port smoke succeeded on both ports:

- `COM5`: `mode=real-port-opened`, `packet_count=1`, `text_bytes=32`, `serial_len=62`.
- `COM8`: `mode=real-port-opened`, `packet_count=1`, `text_bytes=29`, `serial_len=59`.

This proves both connected Pockets can be opened from the Windows desktop and can receive encoded MeshCore companion serial writes. It still does not prove over-LoRa delivery between nodes; that is the next gate.
