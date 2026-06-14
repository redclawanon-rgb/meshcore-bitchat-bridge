# No-hardware smoke transcript regression

This note is for developers refreshing or checking the stable no-hardware smoke transcript fixture.

The smoke path stays local and text-only. It runs the documented demo CLIs through `tools/no_hardware_smoke.py`, invokes `tools/bridge_serial.py` only in its default dry-run mode, and must not open serial, BLE, hardware, network, secrets, or stock bitchat integration.

## Check the fixture

```bash
python3 -m unittest tests.test_no_hardware_smoke_cli -v
```

For the full local regression suite:

```bash
python3 -m unittest discover -s tests -v
```

## Refresh the fixture intentionally

Only refresh after an intentional stable transcript change:

```bash
python3 tools/no_hardware_smoke.py > tests/fixtures/no-hardware-smoke-stable.json
python3 -m unittest tests.test_no_hardware_smoke_cli -v
python3 -m unittest discover -s tests -v
```

Review the fixture diff before committing. Expected stable safety markers include:

- `mode: "no-hardware"` at the transcript level.
- `opens_ble: false`.
- `opens_network: false`.
- `opens_serial: false`.
- `uses_real_hardware: false`.
- `stock_bitchat_compatibility: "not-claimed"`.

Do not automate this with cron, nudge loops, or autoloop behavior; refreshes are explicit developer actions.
