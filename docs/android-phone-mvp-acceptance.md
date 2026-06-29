# Android phone MVP acceptance criteria

## Status

Prepared: 2026-06-29 UTC

This is the acceptance checklist for calling the project a real installable Android phone MVP. It does not itself authorize APK install, BLE, MeshCore transmit, public release, signing-key handling, or production-security claims.

## Acceptance level 1 — install smoke

Required evidence:

- Android checkout commit hash.
- Bridge repo commit hash.
- APK path and filename.
- Phone manufacturer/model, Android release/API level, and ABI, with sensitive identifiers redacted.
- Exact `adb install` command and result.
- Exact launch command or user action.
- Logcat summary.

Pass criteria:

- The APK installs on a named physical Android phone.
- The app launches without crash.
- Mesh bridge behavior remains disabled by default.
- No bridge-originated message is sent or displayed.

## Acceptance level 2 — normal app behavior smoke

Pass criteria:

- Existing bitchat startup behavior is not broken.
- Permission prompts are understandable and expected for the app build.
- No bridge logs/events are emitted while the bridge is disabled.
- No MeshCore bridge transport connects while disabled.
- No unexpected BLE, serial, network, or LoRa behavior is triggered by the bridge code.

## Acceptance level 3 — disabled safety smoke

Pass criteria:

- Inbound public app messages do not leave the app while bridge disabled.
- MeshCore-originated test messages cannot publish into bitchat while bridge disabled.
- Outbound wrapper returns a disabled/rejected result for bridge-originated text.
- Logs make the disabled state visible without printing message contents by default.

## Acceptance level 4 — bridge-enabled debug smoke

This level requires a separate explicit runtime-enable action in a debug build.

Pass criteria:

- Enabling the bridge requires an explicit debug/developer action.
- A visible warning states that the bridge is experimental, public-text-only, and not production secure.
- A public text event accepted by the app emits exactly one bridge event.
- A bridge-originated public text event publishes through the app's normal public-send path.
- Blank and overlong text are rejected before transport/send callbacks.
- Duplicate packet/message IDs are suppressed.
- Queue-full, timeout, and transport-disconnected states produce bounded failures instead of unbounded retries.
- Logs redact peer IDs, nicknames, phone identifiers, Bluetooth identifiers, and message contents unless a separate verbose debug mode is explicitly enabled.

## Acceptance level 5 — two-endpoint field smoke

Pass criteria:

- Endpoint A sends a public test text.
- MeshCore bridge path carries the text.
- Endpoint B or the receiving bridge side observes one delivered public text.
- At least five short public test messages are attempted.
- The report includes delivered count, dropped count, duplicate count, average latency if measurable, app crash count, and relevant redacted logcat/bridge summaries.
- Persistent bridge state and queues are cleanly stopped or reset after the smoke.

## Failure criteria

The phone MVP fails and must not be presented as working if any occur:

- install failure;
- launch crash;
- bridge activation while disabled;
- private/DM/non-public message path becomes bridge-visible;
- unbounded queue growth or retry loop;
- log leakage of secrets or private content;
- bridge text is sent through raw packet/BLE injection instead of the app-owned public-send path;
- the result depends on this VPS emulator path, which Gate 5N already found unreliable.

## Minimum final evidence bundle

A complete phone MVP report should contain:

```text
bridge_repo_commit:
android_repo_commit:
apk_path:
apk_sha256:
phone_model_redacted:
android_api:
abi:
bridge_enabled_default: false
runtime_transport: fake | local_endpoint | meshcore_ble
install_result:
launch_result:
bridge_disabled_smoke_result:
bridge_enabled_debug_smoke_result:
field_smoke_result:
known_failures:
non_claims:
```
