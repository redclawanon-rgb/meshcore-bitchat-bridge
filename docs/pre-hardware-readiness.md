# Pre-hardware readiness / operator handoff

This note is the local handoff between the current no-hardware bridge work and any future gated hardware smoke. It is documentation only: it does not open serial, BLE, hardware, or network paths; it does not handle secrets; it does not add cron, nudge-loop, or autoloop behavior; and it does not claim stock bitchat compatibility or production security.

## Current local readiness map

Before any hardware is considered, the operator should be able to identify and run these local-only checks from the project root.

### 1. No-hardware demo CLIs

- `python3 tools/bridge_sim.py --one-way --alice-text 'smoke test over simulated MeshCore'`
  - Exercises the two-node MeshCore simulator.
  - Expected boundary: `mode: "no-hardware"`; simulated nodes only; no serial/BLE/hardware/network.
- `python3 tools/bridge_serial.py --port /dev/ttyUSB0 'serial smoke'`
  - Encodes MeshCore companion channel-data command bytes and serial TX packet bytes.
  - Expected boundary: `mode: "dry-run-no-port-opened"`; the `--port` value is operator context only; no port is opened unless a later, explicitly approved hardware smoke uses `--open-real-port`.
- `python3 tools/bridge_pump_demo.py`
  - Exercises the fake bridge pump between simulated/fake MeshCore transport and fake semantic bitchat text carrier.
  - Expected boundary: `mode: "no-hardware"`; fake carrier only; no stock `BitchatPacket` compatibility claim.

### 2. Drift-resistant smoke transcript and fixture

- `python3 tools/no_hardware_smoke.py`
  - Runs the documented demo CLIs locally as subprocesses and emits a stable JSON transcript.
  - Expected safety markers include no serial open, no BLE, no network, no real hardware, no secrets, and stock compatibility marked as not claimed.
- `python3 -m unittest tests.test_no_hardware_smoke_cli -v`
  - Checks the stable transcript behavior and fixture comparison.
- `python3 -m unittest discover -s tests -v`
  - Full local regression suite.

The stable fixture is `tests/fixtures/no-hardware-smoke-stable.json`. Refresh it only by explicit developer action as documented in `docs/no-hardware-smoke-regression.md`; do not automate refreshes with cron, nudge loops, or autoloop behavior.

### 3. Gated hardware checklist

`HARDWARE_SMOKE.md` is the only handoff checklist for future real hardware smoke. It requires:

- explicit Eric invocation naming the target setup before any real serial access;
- recording board/model, firmware/source/version, host OS, serial port path, baud, and channel/test-data choices;
- running full tests and a no-port `bridge_serial.py` dry run before opening anything;
- restating the MVP-only/no-production-security/no-secrets boundaries;
- separate approval before the exact guarded `--open-real-port` command;
- capturing command, exit code, output mode, packet lengths, errors, and board observations.

## Non-claims and boundaries

- The bridge remains local/no-hardware by default.
- No serial port is opened by the readiness path.
- No BLE adapter is opened or scanned.
- No hardware is purchased, flashed, accessed, or assumed.
- No network path is needed for these checks.
- No secrets or private production messages are used.
- The bitchat-side MVP seam is semantic public text only.
- Stock bitchat app compatibility/interoperability is not claimed.
- Privacy, Noise, and production-security claims are not made.
- No cron jobs, nudges, autoloops, watchers, or background automation are introduced by this handoff.

## Exact operator handoff sequence

Use this sequence before any future request to touch hardware:

1. Start from a clean local repo state and read `STATUS.md`, `.hermes/context.md`, this note, `docs/no-hardware-smoke-regression.md`, and `HARDWARE_SMOKE.md`.
2. Run the simulator demo:
   ```bash
   python3 tools/bridge_sim.py --one-way --alice-text 'smoke test over simulated MeshCore'
   ```
   Confirm it reports no-hardware simulated delivery.
3. Run the serial dry run:
   ```bash
   python3 tools/bridge_serial.py --port /dev/ttyUSB0 'serial smoke'
   ```
   Confirm `mode` is `dry-run-no-port-opened`, at least one packet is emitted, and no port was opened.
4. Run the fake bridge pump demo:
   ```bash
   python3 tools/bridge_pump_demo.py
   ```
   Confirm fake/no-hardware markers and both-direction pump summaries.
5. Run the stable no-hardware transcript:
   ```bash
   python3 tools/no_hardware_smoke.py
   ```
   Confirm the transcript safety markers remain no-serial/no-BLE/no-network/no-real-hardware and stock compatibility remains not claimed.
6. Run the fixture/full regression checks:
   ```bash
   python3 -m unittest tests.test_no_hardware_smoke_cli -v
   python3 -m unittest discover -s tests -v
   ```
7. If all local checks pass, hand off to `HARDWARE_SMOKE.md` Gate 0. Stop there unless Eric explicitly invokes a hardware smoke run and names the target setup.
8. If Eric does invoke hardware smoke later, follow `HARDWARE_SMOKE.md` exactly. Do not open a real port until the setup is recorded, no-port checks pass, boundaries are restated, and Eric separately approves the guarded `--open-real-port` command.

If any local readiness check fails, stay in the no-hardware path, capture the failing command/output, and fix or reproduce locally before returning to the hardware checklist.
