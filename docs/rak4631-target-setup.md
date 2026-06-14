# RAK4631 target setup notes

Date: 2026-06-14

This records Gate 2B firmware/setup confirmation for Eric's declared target hardware. It is a documentation/preflight artifact only: no serial port was opened, no BLE scan was run, no firmware was flashed, and no hardware was accessed.

## Target hardware from Eric

- Base board: RAK19003 WisBlock base board
- Core board: RAK4631 WisBlock core board
- Antennas: LoRa antenna and BLE antenna present

## Upstream compatibility evidence

Public upstream lookups were performed with GitHub CLI / direct raw HTTP because the configured web-search tool is unavailable in this environment.

Evidence:

- MeshCore upstream repository includes `boards/rak4631.json`.
- `boards/rak4631.json` identifies:
  - USB product: `WisCore RAK4631 Board`
  - MCU: `nrf52840`
  - CPU: `cortex-m4`
  - upload speed: `115200`
  - upload protocol: `nrfutil`
  - connectivity includes `bluetooth`
  - hardware IDs include Adafruit/Rak nRF52840 CDC/bootloader IDs such as `0x239A:0x8029`, `0x239A:0x0029`, `0x239A:0x002A`, `0x239A:0x802A`
- MeshCore `variants/rak4631/variant.h` identifies RAK4631 LoRa SX1262 pin mapping and notes RAK4631 has no buttons.
- MeshCore FAQ lists RAK Wireless WisBlock RAK4631 devices including 19003 as supported MeshCore hardware.
- MeshCore flasher config contains a RAK4631 device entry with bootloader `wiscore_rak4631_board_bootloader-0.9.2-OTAFIX2.1.uf2` and firmware roles:
  - `companionBle`
  - `companionUsb`
  - `repeater`
  - `roomServer`

## Candidate firmware for this bridge path

For this project, the first hardware smoke should prefer the **USB Serial Companion** firmware because the local bridge currently targets MeshCore companion datagrams over a serial-first transport seam.

Latest observed MeshCore companion release via GitHub:

- Release: `Companion Firmware v1.16.0`
- Tag: `companion-v1.16.0`
- Date observed from GitHub release list: `2026-06-06`
- RAK4631 assets observed:
  - `RAK_4631_companion_radio_usb-v1.16.0-07a3ca9.uf2`
  - `RAK_4631_companion_radio_usb-v1.16.0-07a3ca9.zip`
  - `RAK_4631_companion_radio_ble-v1.16.0-07a3ca9.uf2`
  - `RAK_4631_companion_radio_ble-v1.16.0-07a3ca9.zip`

Use USB companion first for Gate 2C serial smoke. BLE companion is relevant later for the BLE exploration gate.

## Physical setup checks before connection

Before powering or connecting hardware:

- Confirm the LoRa antenna is connected to the LoRa antenna port before any LoRa transmit-capable firmware use.
- Confirm the BLE antenna is connected if using BLE paths later.
- Confirm the RAK4631 core board is seated correctly on the RAK19003 base board.
- Use a known-good USB data cable, not charge-only.
- Avoid running any `--open-real-port` command until the exact device path is identified.

## Expected host-side signs after USB connection

When connected to the Linux host, expected candidate serial paths may include:

- `/dev/ttyACM0`
- `/dev/ttyUSB0`
- `/dev/serial/by-id/...`
- `/dev/serial/by-path/...`

Prefer a stable `/dev/serial/by-id/...` path if available.

The current VPS/session inventory found no candidate serial devices, so hardware is not yet visible here.

## Next Gate 2 steps

1. Connect the RAK19003 + RAK4631 assembly with antennas attached to the target host using a USB data cable.
2. Re-run Gate 2A device inventory.
3. Record exact serial path and firmware state.
4. If firmware is not already MeshCore USB Serial Companion, decide whether to flash using the MeshCore flasher / UF2 / nRFUtil path. Flashing is a separate hardware/firmware action and should be explicit.
5. Run the project no-hardware checks again.
6. Run `tools/bridge_serial.py --port <identified-port> 'serial smoke'` without `--open-real-port` first.
7. Only after the exact port/firmware/device are confirmed, run a guarded `--open-real-port` smoke if Eric explicitly approves that exact invocation.

## Current stop point

Stopped before hardware access. No serial port was opened, no BLE scan occurred, and no firmware was flashed.
