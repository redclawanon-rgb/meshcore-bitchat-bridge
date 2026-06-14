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

This proves both connected Pockets can be opened from the Windows desktop and can receive encoded MeshCore companion serial writes.

## Gate 2D: two-node over-LoRa delivery

A gated live two-port utility was added at `tools/live_lora_smoke.py`. It opens a transmit port and receive port only when `--open-real-ports` is passed, sends a MeshCore channel-data datagram, listens for MeshCore serial frames on the receiver, handles `PUSH_CODE_MSG_WAITING` (`0x83`) by polling `CMD_SYNC_NEXT_MESSAGE` (`0x0A`), and decodes `RESP_CODE_CHANNEL_DATA_RECV` (`0x1B`) into bridge text.

The first live attempt saw RF activity but did not poll queued messages yet: both receivers emitted `PUSH_CODE_LOG_RX_DATA` (`0x88`) and `PUSH_CODE_MSG_WAITING` (`0x83`). Upstream docs/source confirmed `0x83` means the host must poll `CMD_SYNC_NEXT_MESSAGE` to retrieve queued datagrams.

After adding message polling, two-way over-LoRa delivery succeeded:

### COM5 / pocket-1 to COM8 / pocket-2

Command:

```powershell
python tools/live_lora_smoke.py --tx-port COM5 --rx-port COM8 --open-real-ports --listen-seconds 30 'gate2d COM5 to COM8 poll smoke'
```

Verified output included:

- `mode`: `real-ports-opened`
- `tx_port`: `COM5`
- `rx_port`: `COM8`
- `notification_count`: `3`
- notification types: `log_rx_data`, `msg_waiting`, `channel_data_recv`
- `delivered_count`: `1`
- decoded text: `gate2d COM5 to COM8 lora smoke`
- `parse_errors`: `[]`

### COM8 / pocket-2 to COM5 / pocket-1

Command:

```powershell
python tools/live_lora_smoke.py --tx-port COM8 --rx-port COM5 --open-real-ports --listen-seconds 30 'gate2d COM8 to COM5 poll smoke'
```

Verified output included:

- `mode`: `real-ports-opened`
- `tx_port`: `COM8`
- `rx_port`: `COM5`
- `notification_count`: `3`
- notification types: `log_rx_data`, `msg_waiting`, `channel_data_recv`
- `delivered_count`: `1`
- decoded text: `gate2d COM8 to COM5 lora smoke`
- `parse_errors`: `[]`

This proves actual bidirectional over-LoRa delivery of the bridge-encoded text payload between the two MeshCore-flashed WisMesh Pockets, via the Windows desktop serial bridge path.

## Gate 2E: 20-message bidirectional stability loop

A gated stability runner was added at `tools/live_lora_stability.py`. It alternates one-message `live_lora_smoke` attempts between two ports, records per-message latency, delivery status, notification frame types, parse errors, duplicate deliveries, and aggregate delivery rate. It defaults to dry-run/no-open mode and requires `--open-real-ports` for live hardware.

Live command run on the Windows desktop:

```powershell
python tools/live_lora_stability.py --port-a COM5 --port-b COM8 --count 20 --listen-seconds 8 --pause-seconds 0.25 --open-real-ports
```

Verified aggregate result:

- `mode`: `real-ports-opened`
- `count`: `20`
- `delivered`: `20`
- `failed`: `0`
- `delivery_rate`: `1.0`
- `duplicate_deliveries`: `0`
- `parse_error_count`: `0`
- notification type counts:
  - `log_rx_data`: `20`
  - `msg_waiting`: `20`
  - `channel_data_recv`: `20`
- latency seconds:
  - min: `0.8589999999967404`
  - avg: `0.8749499999976251`
  - median: `0.875`
  - max: `0.8910000000032596`

All 20 attempts alternated directions:

- odd attempts: `COM5` / `pocket-1` to `COM8` / `pocket-2`
- even attempts: `COM8` / `pocket-2` to `COM5` / `pocket-1`

Each attempt delivered exactly one decoded text payload and saw the expected notification sequence `log_rx_data`, `msg_waiting`, `channel_data_recv`.

This proves a short bidirectional LoRa reliability loop is stable under the current desk/test conditions. It still does not prove long-duration daemon behavior, mobile/stock bitchat compatibility, or performance under range/interference/load.

## Gate 2F: continuous MeshCore-side daemon skeleton

A gated continuous daemon skeleton was added at `tools/meshcore_bridge_daemon.py`. It opens one or more named MeshCore USB Companion serial ports only when `--open-real-ports` is passed, continuously reads serial frames, classifies companion frame types, polls `CMD_SYNC_NEXT_MESSAGE` after `msg_waiting` and after each `channel_data_recv` so queued messages are drained, decodes bridge text payloads, emits structured JSON events, and closes ports cleanly. It does not implement the real bitchat side yet.

The daemon defaults to dry-run/no-open mode. Dry-run example:

```powershell
python tools/meshcore_bridge_daemon.py --port pocket1=COM5 --port pocket2=COM8 --inject-text pocket1:'dry run daemon' --duration-seconds 1
```

Verified dry-run output included:

- `mode`: `dry-run-no-ports-opened`
- `event_count`: `1`
- first event: `daemon_plan`
- `delivered_count`: `0`
- `parse_error_count`: `0`

Live smoke command on the Windows desktop:

```powershell
python tools/meshcore_bridge_daemon.py --port pocket1=COM5 --port pocket2=COM8 --inject-text pocket1:'gate2f daemon final smoke' --duration-seconds 5 --open-real-ports
```

Verified live output included:

- `mode`: `real-ports-opened`
- `ports`: `pocket1=COM5`, `pocket2=COM8`
- `injection_count`: `1`
- `delivered_count`: `1`
- `parse_error_count`: `0`
- `message_id_start`: time-derived (`63624` in the verified run), preventing daemon restart collisions with queued older message IDs
- events included:
  - `port_opened` for both ports
  - `injected_text` on `pocket1` / `COM5`
  - `ok` response on `pocket1`
  - `log_rx_data` and `msg_waiting` on `pocket2`
  - `channel_data_recv` on `pocket2`
  - decoded delivered text: `gate2f daemon final smoke`
  - follow-up `no_more_messages` after draining the queue
  - `port_closed` for both ports

Two daemon-specific issues were discovered and fixed during live testing:

1. Windows serial ports are exclusive, so injected daemon text must write through the already-open serial handle rather than opening the TX port a second time.
2. Restarting a daemon with message ID `1` can collide with older queued messages from the same bridge ID, causing fresh messages to be deduped. The daemon now uses a time-derived default `message_id_start`, with `--message-id-start` available for explicit control.

This proves the MeshCore side now has a minimal continuous event-loop spine. It is still a skeleton: it does not yet persist queues, reconnect after device disconnects, expose a long-running service wrapper, or connect to a real bitchat-side adapter.

## Gate 2G: daemon state/log hardening

The MeshCore daemon was hardened with:

- `--event-log PATH`: append-only JSONL event log with one structured event per line.
- `--state-file PATH`: persistent JSON state containing `next_message_id` and per-port bridge/message-id metadata.
- reconnect-aware port handling:
  - failed opens emit `port_open_failed` and retry after `--reconnect-interval-seconds`.
  - read/write/poll errors close only the affected port and schedule reconnect.
  - normal shutdown still emits clean `port_closed` events.
- startup state loading:
  - if the state file has `next_message_id`, it overrides the time-derived fallback.
  - this prevents daemon restarts from reusing message IDs and colliding with queued/deduped prior messages.

Local tests added coverage for dry-run JSONL logging and state-file message ID loading. Full local test suite passed with `65` tests.

Live command run on the Windows desktop:

```powershell
python tools/meshcore_bridge_daemon.py \
  --port pocket1=COM5 \
  --port pocket2=COM8 \
  --inject-text pocket1:'gate2g hardened daemon smoke' \
  --duration-seconds 6 \
  --event-log .hermes\\runtime\\gate2g-events.jsonl \
  --state-file .hermes\\runtime\\gate2g-state.json \
  --open-real-ports
```

Verified first live result:

- `mode`: `real-ports-opened`
- `delivered_count`: `1`
- `parse_error_count`: `0`
- `reconnect_count`: `0`
- delivered text on `pocket2`: `gate2g hardened daemon smoke`
- `event_log`: `.hermes\\runtime\\gate2g-events.jsonl`
- JSONL lines after first run: `16`
- `state_file`: `.hermes\\runtime\\gate2g-state.json`
- state saved `next_message_id`: `64113`

Then the daemon was run again against the same state file:

```powershell
python tools/meshcore_bridge_daemon.py \
  --port pocket1=COM5 \
  --port pocket2=COM8 \
  --inject-text pocket1:'gate2g persisted state smoke' \
  --duration-seconds 6 \
  --event-log .hermes\\runtime\\gate2g-events.jsonl \
  --state-file .hermes\\runtime\\gate2g-state.json \
  --open-real-ports
```

Verified second live result:

- `state_loaded`: `true`
- `message_id_start`: `64113`
- delivered text on `pocket2`: `gate2g persisted state smoke`
- delivered message ID: `64113`
- final state saved `next_message_id`: `64114`
- JSONL lines after second run: `32`
- `delivered_count`: `1`
- `parse_error_count`: `0`
- `reconnect_count`: `0`

This proves the daemon can persist event/state files across runs and avoid restart message ID reuse under the current two-Pocket desk test conditions.

## Gate 2H: live unplug/replug reconnect test

Live physical mapping confirmed that the screen ID `D0521521` corresponds to `pocket2` / `COM8`. During the reconnect test, Eric unplugged that device, waited, and plugged it back in.

Reconnect-window command:

```powershell
python tools/meshcore_bridge_daemon.py \
  --port pocket1=COM5 \
  --port pocket2=COM8 \
  --duration-seconds 180 \
  --reconnect-interval-seconds 3 \
  --event-log .hermes\\runtime\\gate2h-reconnect-events.jsonl \
  --state-file .hermes\\runtime\\gate2h-reconnect-state.json \
  --open-real-ports
```

Verified reconnect event summary:

- JSONL event lines: `17`
- event kinds:
  - `daemon_plan`: `1`
  - `port_opened`: `3`
  - `serial_read_error`: `1`
  - `port_closed`: `3`
  - `port_open_failed`: `8`
  - `state_saved`: `1`
- `COM8` opened at start.
- unplug produced `serial_read_error` on `COM8`:
  - `ClearCommError failed (PermissionError(13, 'The device does not recognize the command.', None, 22))`
- daemon closed only `pocket2` / `COM8` with reason `read_error`.
- while unplugged, daemon emitted eight `port_open_failed` events for `COM8` with `FileNotFoundError(2, 'The system cannot find the file specified.', None, 2)`.
- after replug, daemon emitted `port_opened` for `pocket2` / `COM8` at monotonic timestamp `397282.609`.
- final summary reported `reconnect_count`: `8`, `parse_error_count`: `0`.

Post-reconnect delivery smoke:

```powershell
python tools/meshcore_bridge_daemon.py \
  --port pocket1=COM5 \
  --port pocket2=COM8 \
  --inject-text pocket1:'gate2h post reconnect delivery' \
  --duration-seconds 6 \
  --reconnect-interval-seconds 3 \
  --event-log .hermes\\runtime\\gate2h-post-reconnect-events.jsonl \
  --state-file .hermes\\runtime\\gate2h-reconnect-state.json \
  --open-real-ports
```

Verified post-reconnect delivery:

- `state_loaded`: `true`
- `message_id_start`: `64573`
- `delivered_count`: `1`
- `parse_error_count`: `0`
- `reconnect_count`: `0`
- delivered text on `pocket2`: `gate2h post reconnect delivery`
- delivered message ID: `64573`
- final state saved `next_message_id`: `64574`

This proves live unplug/replug recovery for the current two-Pocket desk test: the daemon detected loss of `COM8`, closed only the affected port, retried while absent, reopened it after replug, and subsequently delivered a fresh MeshCore message over the recovered port.
