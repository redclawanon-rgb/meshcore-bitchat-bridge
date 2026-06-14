# Gated next loops / post-MVP playbook map

This document maps the post-MVP paths that are **not active by default**. It is a local planning artifact only: creating or reading it does not authorize any public push/post, hardware purchase/flashing/use, serial/BLE access, secrets handling, stock bitchat compatibility implementation, or production/security claim.

Every loop below requires a fresh explicit instruction from Eric naming the gate to open. If the instruction is ambiguous, stop and ask before touching the gated surface.

## Recommended order

1. **Public repository prep / release hygiene** — only if Eric wants a public repo or public post.
2. **Hardware smoke** — purchase/choose/flash/use hardware only after a named hardware setup is approved.
3. **Real serial adapter smoke** — after hardware is present and no-hardware checks still pass.
4. **BLE exploration** — after serial path evidence exists, unless Eric explicitly prioritizes BLE first.
5. **Stock bitchat compatibility research** — version-pinned research before any implementation or interoperability claim.
6. **Production/security review and claims** — last, after live transport and compatibility scopes are proven and reviewed.

## Global gate rules

- No gate is active unless Eric explicitly picks it in the current conversation or task.
- Run local no-hardware checks before and after a gated loop when practical.
- Capture exact commands, environment, versions, logs, device identifiers, and diffs as evidence.
- Keep secrets out of tracked files, logs, screenshots, fixtures, and prompts.
- Prefer short, reversible loops with a written stop point over open-ended exploration.
- If a loop touches hardware, serial, BLE, public network, public repository state, secrets, stock compatibility, or security claims beyond local lab scope, stop unless that exact surface is authorized.

## Gate 1: public repository prep / public post

### Trigger / explicit authorization required

Eric explicitly asks to create/push a public repository, publish a branch/tag/release, or make a public post/announcement.

### Preflight checks

- Confirm target remote, visibility, branch, license, README wording, and whether issues/wiki/releases are enabled.
- Review `README.md`, `STATUS.md`, `THREAT_MODEL.md`, `BITCHAT_SEAM.md`, `docs/mvp-handoff-index.md`, and this file for non-claims.
- Run `git status --short` and ensure only intended changes are present.
- Run the full local test suite.
- Scan docs for accidental secrets, private paths, personal tokens, unsupported compatibility claims, and production/security language.

### Bounded loop steps once authorized

1. Create or configure the remote exactly as authorized.
2. Push only the approved branch/tag.
3. If a public post is requested, draft it locally first and get wording approval unless Eric explicitly delegates final wording.
4. Publish only after verifying the final URL/visibility matches the authorization.

### Verification/evidence to capture

- `git status --short` before push.
- Full unittest output.
- Remote URL/visibility summary.
- Commit hash, branch, tag/release URL, and/or public post URL.
- Final public wording snapshot if a post is made.

### Stop/rollback criteria

- Stop if remote visibility, ownership, license, or push target is unclear.
- Stop if tests fail or the working tree has unexpected changes.
- Stop if docs imply stock bitchat compatibility, privacy, production readiness, or security beyond lab/local scope.
- Roll back by deleting mistaken tags/releases/posts or reverting public wording only with explicit approval for those public actions.

### Files/docs likely affected

- `README.md`
- `STATUS.md`
- `THREAT_MODEL.md`
- `docs/mvp-handoff-index.md`
- Release notes or announcement drafts
- Git remote/branch/tag metadata

## Gate 2: hardware smoke

### Trigger / explicit authorization required

Eric explicitly approves hardware purchase, hardware selection, flashing, physical setup, and/or a hardware smoke run. Authorization should name the boards/devices and whether purchase, flashing, or only local documentation is allowed.

### Preflight checks

- Confirm hardware model, firmware source/version, cable/power setup, host OS access, and expected MeshCore settings.
- Read `docs/pre-hardware-readiness.md` and `HARDWARE_SMOKE.md`.
- Run no-hardware demos and the full local test suite.
- Confirm no real serial command will be run until the later explicit serial-open step is approved.
- Record baseline git status and current commit.

### Bounded loop steps once authorized

1. Prepare a hardware-specific smoke plan from `HARDWARE_SMOKE.md`.
2. If flashing is authorized, record exact firmware image/source, version, commands, and observed device behavior.
3. Perform only the approved physical setup checks.
4. Stop before any unapproved serial/BLE access or live message transmission.

### Verification/evidence to capture

- Board model(s), firmware version(s), flashing commands, and checksums where applicable.
- Photos/log snippets only if they contain no secrets or private identifiers.
- No-hardware test output before/after setup.
- Notes on power, cable, serial device enumeration, and any failures.

### Stop/rollback criteria

- Stop if board identity, firmware source, or flashing target is uncertain.
- Stop on smoke, heat, unstable power, unexpected bootloader state, or device enumeration anomalies.
- Stop before opening any real port unless separately approved.
- Roll back by restoring documented firmware/config only when Eric approves that rollback action.

### Files/docs likely affected

- `HARDWARE_SMOKE.md`
- `docs/pre-hardware-readiness.md`
- `STATUS.md`
- `DECISIONS.md` if target hardware choice becomes a project decision
- New local evidence note under `evidence/` if approved

## Gate 3: real serial adapter smoke

### Trigger / explicit authorization required

Eric explicitly approves opening a named serial device and running a named real-port command, e.g. a `tools/bridge_serial.py --open-real-port --port ...` smoke. Hardware must already be physically present and expected to be safe to access.

### Preflight checks

- Confirm exact serial path, baud, device ownership/permissions, and target node state.
- Run the dry-run serial command first without `--open-real-port`.
- Run `python3 -m unittest discover -s tests -v`.
- Confirm the command will not transmit private content or secrets.
- Confirm logging redaction strategy before capturing serial output.

### Bounded loop steps once authorized

1. Run one minimal real-port open/write/read smoke exactly as authorized.
2. Capture raw command, return code, and sanitized output.
3. If successful, run one bounded end-to-end adapter check only if included in the authorization.
4. Return to dry-run/no-hardware checks after the live access.

### Verification/evidence to capture

- Exact real-port command and return code.
- Sanitized serial logs or packet hex.
- Device path, baud, firmware version, and host permissions summary.
- Before/after full unittest result.

### Stop/rollback criteria

- Stop if the port path changes unexpectedly or another process owns the device.
- Stop on timeout, malformed response, repeated CRC/frame errors, or unexpected transmit behavior.
- Stop before trying alternative ports, baud rates, or message contents unless separately approved.
- Roll back code/doc changes if the smoke shows the implementation assumptions were wrong.

### Files/docs likely affected

- `tools/bridge_frame_codec/serial_adapter.py`
- `tools/bridge_serial.py`
- `tests/test_serial_adapter.py`
- `HARDWARE_SMOKE.md`
- `STATUS.md`
- Evidence notes under `evidence/` if approved

## Gate 4: BLE exploration

### Trigger / explicit authorization required

Eric explicitly approves BLE adapter scanning/connection or BLE implementation work, naming the host adapter/device scope and whether passive discovery, connection, or code changes are allowed.

### Preflight checks

- Confirm adapter identity, OS permissions, radio environment, and target device names/addresses if known.
- Review `ADAPTER.md` and MeshCore companion BLE protocol references.
- Run local tests before BLE access.
- Define scan duration, connection target, and data to capture.
- Confirm no broad public BLE scan or connection to unknown third-party devices is intended.

### Bounded loop steps once authorized

1. Perform the shortest approved BLE scan or connection attempt.
2. Record service/characteristic metadata needed for the companion datagram seam.
3. Implement or adjust only the minimal BLE adapter seam if implementation is authorized.
4. Add fake/unit tests first where possible; keep live BLE smoke separate and explicit.

### Verification/evidence to capture

- Adapter/device identifiers, scan duration, service UUIDs, characteristic UUIDs, and sanitized logs.
- Unit tests for any BLE adapter code using fakes/mocks.
- Full local unittest output after code/doc changes.
- A clear statement of whether any live BLE connection occurred.

### Stop/rollback criteria

- Stop if target identity is ambiguous or third-party devices dominate scan results.
- Stop on permissions errors that require broad system changes unless Eric approves them.
- Stop before repeated scans or connection retries outside the authorized bound.
- Roll back experimental code if it weakens no-hardware defaults or opens BLE by default.

### Files/docs likely affected

- `ADAPTER.md`
- Future BLE adapter module under `tools/bridge_frame_codec/`
- Future BLE CLI or smoke doc
- Tests for fake BLE behavior
- `STATUS.md`

## Gate 5: stock bitchat compatibility research

### Trigger / explicit authorization required

Eric explicitly asks for scoped stock bitchat compatibility research or implementation. The request should name upstream repository/version/commit and whether the work is research-only, fixture-only, or implementation.

### Preflight checks

- Pin upstream bitchat source version/commit and record license/compatibility constraints.
- Re-read `BITCHAT_SEAM.md` and `DECISIONS.md` D005.
- Define what “compatibility” means: packet bytes, BLE behavior, public-channel semantics, conformance fixtures, or app interoperability.
- Confirm no production interoperability claim will be made from research alone.
- Run full local tests before changes.

### Bounded loop steps once authorized

1. Capture upstream packet/message/BLE evidence at the pinned version.
2. Create local notes and fixtures that distinguish observed upstream behavior from bridge behavior.
3. If implementation is authorized, add the smallest compatibility shim behind explicit tests and no live BLE by default.
4. Update non-claims unless actual interoperability has been tested under an approved live loop.

### Verification/evidence to capture

- Upstream commit hash, files inspected, and relevant excerpts/links.
- New conformance fixtures and unit tests.
- Full local unittest output.
- Explicit compatibility status: research-only, partial fixture compatibility, or live-tested interop if separately authorized.

### Stop/rollback criteria

- Stop if upstream version, license posture, or compatibility target is unclear.
- Stop before using real BLE/stock apps unless that separate live gate is approved.
- Stop if implementation would imply unsupported privacy/security/interoperability claims.
- Roll back or isolate code that forges stock packets without sufficient fixtures and review.

### Files/docs likely affected

- `BITCHAT_SEAM.md`
- `DECISIONS.md`
- New evidence note under `evidence/`
- New compatibility fixtures under `tests/fixtures/`
- New codec/shim tests and modules if implementation is authorized
- `README.md` and `STATUS.md` non-claims

## Gate 6: secrets handling

### Trigger / explicit authorization required

Eric explicitly asks to use, configure, rotate, or document real secrets, credentials, tokens, private keys, API keys, deployment credentials, or private production messages.

### Preflight checks

- Confirm the minimum secret needed and where it should live outside git.
- Confirm `.gitignore` coverage and redaction rules before any command runs.
- Decide whether a throwaway/test credential can replace a real one.
- Ensure logs, fixtures, screenshots, and prompts will not capture raw secret values.

### Bounded loop steps once authorized

1. Use environment variables, local ignored config, or an approved secret manager only.
2. Validate with a minimal command that does not print the secret.
3. Document placeholders and setup steps, never secret values.
4. Rotate/revoke immediately if any accidental exposure occurs.

### Verification/evidence to capture

- Redacted command transcript.
- Confirmation that tracked files contain placeholders only.
- `git status --short` and secret scan result if tools are available/approved.
- Rotation/revocation record if exposure happens.

### Stop/rollback criteria

- Stop if the secret source, storage location, or redaction plan is unclear.
- Stop if a tool would echo or upload raw secrets.
- Stop and rotate/revoke if any secret enters tracked files, logs, prompt text, or public output.

### Files/docs likely affected

- `.gitignore`
- Example config templates
- `README.md` setup notes
- `THREAT_MODEL.md`
- `STATUS.md`

## Gate 7: production/security review and claims

### Trigger / explicit authorization required

Eric explicitly asks for a production readiness review, security review, privacy claim, Noise/cryptography claim, deployment hardening, or public security language.

### Preflight checks

- Define the claim surface and audience: lab demo, beta, production, privacy, cryptography, transport security, or operational security.
- Review `THREAT_MODEL.md`, `PROTOCOL.md`, `DECISIONS.md`, and compatibility/live evidence.
- Confirm whether external review, fuzzing, hardware testing, stock app testing, and threat-model updates are in scope.
- Run full local tests and identify missing security tests.

### Bounded loop steps once authorized

1. Inventory assets, trust boundaries, data flows, attack surfaces, and non-goals.
2. Add tests/docs for concrete mitigations only when evidence exists.
3. Draft conservative claim language separately from implementation notes.
4. Require explicit approval before publishing or presenting security/privacy claims.

### Verification/evidence to capture

- Updated threat model and claim matrix.
- Test/fuzz/static-analysis output if run.
- Live hardware/compatibility evidence only if separately authorized and already captured.
- Final approved public language if publication is authorized.

### Stop/rollback criteria

- Stop if requested claim exceeds implemented/tested behavior.
- Stop if cryptographic or privacy claims lack external review or evidence.
- Stop before public release language unless public-post/repo gate is also approved.
- Roll back or downgrade unsupported claims to explicit non-claims.

### Files/docs likely affected

- `THREAT_MODEL.md`
- `PROTOCOL.md`
- `README.md`
- `STATUS.md`
- `DECISIONS.md`
- New security evidence/review notes under `evidence/` if approved

## Default next choice

If Eric wants the least risky next gated move, choose **public repository prep / release hygiene** first, because it can remain mostly local until the final push/post authorization. If Eric wants technical validation instead, choose **hardware smoke** followed by **real serial adapter smoke**.
