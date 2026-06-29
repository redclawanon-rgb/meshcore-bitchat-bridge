# Local MVP handoff index / release-readiness note

This is the operator-facing index for the current local MVP state. It is a documentation-only handoff: it does not open serial, BLE, hardware, or network paths; it does not handle secrets; it does not add cron, nudge-loop, autoloop, watcher, or background automation behavior; and it does not claim stock bitchat compatibility, interoperability, privacy, Noise coverage, or production security.

## Start here

1. Read `STATUS.md` for current milestone, verified commands, blockers, and the next loop/gate.
2. Read `.hermes/context.md` for continuity across local agent/human sessions.
3. Read `DECISIONS.md` for the locked MVP choices and still-pending decisions.
4. Run only the local no-hardware checks listed below unless Eric explicitly invokes a gated hardware smoke.

## Release-readiness map

### Protocol and payload contract

- `PROTOCOL.md` — bridge-frame v0, including frame fields, CRC, fragmentation budget, and canonical vector expectations.
- `tests/vectors/bridge-frame-v0.json` — canonical local vector for the v0 codec.
- `evidence/meshcore-payload-budget.md` — recorded MeshCore companion payload budget evidence used by the protocol.

Current readiness: local codec, fragmentation helpers, CLI, simulator, and companion channel-data wrappers are covered by tests. The MVP uses MeshCore companion channel-data datagrams with development `data_type = 0xFFFF` and does not claim a registered production namespace.

### Adapter decisions and seams

- `ADAPTER.md` — transport-neutral companion datagram seam; serial is the first future live adapter target, BLE second.
- `DECISIONS.md` — D003, D004, and D005 capture the MeshCore carrier, adapter path, and bitchat-side semantic text-only seam.
- `BITCHAT_SEAM.md` — public bitchat-source seam notes and the MVP boundary for a future semantic public-text carrier.
- `tools/bridge_frame_codec/transport.py` — local fake companion-datagram transport.
- `tools/bridge_frame_codec/serial_adapter.py` — serial packet wrapper/parser and guarded no-open serial transport scaffold.
- `tools/bridge_frame_codec/bitchat_text.py` — fake semantic bitchat-side public text carrier.
- `tools/bridge_frame_codec/bridge_pump.py` — no-hardware text bridge pump between delivered MeshCore text and the semantic carrier.

Current readiness: adapter seams are locally testable with fake streams/carriers. Real serial remains guarded by explicit `--open-real-port` approval. BLE is not implemented or opened.

### No-hardware operator demos

From the project root:

```bash
python3 tools/bridge_sim.py --one-way --alice-text 'smoke test over simulated MeshCore'
python3 tools/bridge_serial.py --port /dev/ttyUSB0 'serial smoke'
python3 tools/bridge_pump_demo.py
python3 tools/no_hardware_smoke.py
```

Expected boundary:

- `bridge_sim.py`, `bridge_pump_demo.py`, and `no_hardware_smoke.py` stay local/fake/simulated.
- `bridge_serial.py` is dry-run by default and reports `mode: "dry-run-no-port-opened"`.
- No serial port, BLE adapter, hardware, network, or secrets are accessed by these checks.
- The fake bitchat-side carrier is semantic text-only and does not forge stock `BitchatPacket` bytes.

### Smoke regression fixture

- `tests/fixtures/no-hardware-smoke-stable.json` — pinned stable no-hardware transcript fields.
- `docs/no-hardware-smoke-regression.md` — explicit developer check/refresh instructions.
- `tests/test_no_hardware_smoke_cli.py` — fixture comparison and smoke transcript tests.

Check commands:

```bash
python3 -m unittest tests.test_no_hardware_smoke_cli -v
python3 -m unittest discover -s tests -v
```

Refreshes are explicit developer actions only. Do not add cron, nudge loops, autoloops, watchers, or other automation to refresh or enforce this fixture.


### Phone MVP build spec

The next installable-cell-phone target is an Android physical-phone debug APK, not iOS or public release packaging. The phone path is now specified across these docs:

- `docs/phone-platform-scope.md` — first phone platform scope and deferred iOS/release-store work.
- `docs/phone-runtime-architecture.md` — Android debug runtime architecture and transport choices.
- `docs/android-phone-mvp-acceptance.md` — install, disabled-safety, bridge-enabled debug, and two-endpoint acceptance criteria.
- `docs/android-packaging-plan.md` — debug APK packaging, ABI selection, version labels, and signing/distribution boundaries.
- `docs/android-phone-security-boundary.md` — warning, log redaction, and security boundary requirements.
- `docs/bridge-queueing-spec.md` — bounded queueing, duplicate suppression, retry, timeout, and telemetry requirements.

Current readiness: this is a build specification for the remaining phone work. It does not install or run an APK, open BLE/serial, transmit LoRa traffic, publish artifacts, or claim production security/interoperability.

### Pre-hardware readiness and gated hardware path

- `docs/pre-hardware-readiness.md` — exact local sequence before any future hardware request.
- `HARDWARE_SMOKE.md` — the only checklist for a later real hardware smoke.

The hardware path is gated. Stop at local dry-runs unless Eric explicitly asks for a hardware smoke run, names the target setup, and later separately approves the exact guarded `--open-real-port` command after setup/no-port checks are recorded.

## Current blockers and non-claims

Blockers before any live/hardware release work:

- Hardware availability is not confirmed.
- Target boards are not chosen.
- GitHub remote/public release path is not created or approved.
- Real stock bitchat integration remains unscoped and unclaimed; future work needs version-pinned upstream API/conformance decisions.
- MVP security remains lab/local only; no production-security, privacy, Noise, or stock interoperability claims are made.
- Long-term app namespace remains pending; the MVP uses development `data_type = 0xFFFF`.

Non-claims and safety boundaries:

- No stock bitchat app compatibility/interoperability claim.
- No production readiness/security/privacy claim.
- No real serial/BLE/hardware/network path in this local handoff.
- No secrets or private production messages.
- No automation/cron/nudge/autoloop behavior.

## Human operator summary

The local MVP is release-ready only as a no-hardware, text-only bridge-frame and adapter-seam demonstration with regression coverage. A future operator can verify it entirely from local docs, CLIs, fixtures, and tests. Any move beyond that point is a real gate: public push/post, hardware purchase/flashing/use, secrets, production/security claims, real serial access, or BLE access require separate explicit approval.
