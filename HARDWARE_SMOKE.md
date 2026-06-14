# Gated Hardware Smoke Checklist

This project remains local/no-hardware by default. Do not open a serial port, flash a board, purchase hardware, or make production/security claims unless Eric explicitly invokes that hardware smoke step.

## Gate 0 — explicit invocation required

Proceed only when Eric explicitly asks for a hardware smoke run and names the target setup. Without that invocation, stop at dry-runs and fake-stream tests.

## Gate 1 — identify the setup

Record before any real serial access:

- Board/model: `TBD`
- Firmware/source and version/commit: `TBD`
- Host OS: `TBD`
- Serial port path: `TBD` (for example `/dev/ttyUSB0` or `/dev/ttyACM0`)
- Baud rate: `115200` unless Eric confirms otherwise
- Channel/index and test data type: development-only defaults unless changed intentionally

## Gate 2 — run no-port checks first

From the project root, verify local tests and a dry-run packet before opening anything:

```bash
python3 -m unittest discover -s tests -v
python3 tools/bridge_serial.py --port /dev/ttyUSB0 'hardware smoke dry run'
```

Expected dry-run properties:

- Output mode is `dry-run-no-port-opened`.
- At least one packet is emitted.
- `serial_tx_hex` starts with `3c`.
- No serial port is opened.

## Gate 3 — claims and safety review

Before the real-port command:

- State that this is an MVP smoke test only.
- Do not describe the bridge as production-ready or secure.
- Do not use secrets or private production messages.
- Use a harmless test string such as `hardware smoke test`.
- Confirm the chosen port belongs to the intended board.

## Gate 4 — exact real-port command, only after approval

After Eric explicitly approves opening the identified port, run exactly the guarded path with `--open-real-port`:

```bash
python3 tools/bridge_serial.py --port /dev/ttyUSB0 --baud 115200 --open-real-port 'hardware smoke test'
```

Replace `/dev/ttyUSB0` only with the approved, identified port. Do not bypass the `--open-real-port` guard or instantiate `open_real_port=True` from ad hoc scripts unless Eric separately approves that exact invocation.

## Gate 5 — capture results

Record:

- Command used.
- Exit code.
- JSON output mode (`real-port-opened` expected for the guarded real-port command).
- Packet count and companion command lengths.
- Any serial/permission errors verbatim.
- Whether the board showed any expected receive/transmit indication.

If anything unexpected happens, stop and return to no-hardware/fake-stream reproduction before another real-port attempt.
