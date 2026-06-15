# Gate 5M — Android runtime/device preflight checklist

## Status

Prepared locally: 2026-06-15 EDT

Gate 5M is a preflight checklist for a future Android install/run gate. It does not install, start, interact with, or enable the app. It records the safest next runtime path after Gates 5G-5L proved the disabled app-side seams and debug APK packaging.

## Current local artifacts

Android checkout:

```text
repo: /tmp/bitchat-android
branch: gate5g-android-adapter-stub
HEAD: 55ad1b5 Add disabled Mesh bridge outbound wrapper
```

Debug APK artifacts produced by Gate 5L:

```text
app/build/outputs/apk/debug/app-arm64-v8a-debug.apk
app/build/outputs/apk/debug/app-armeabi-v7a-debug.apk
app/build/outputs/apk/debug/app-universal-debug.apk
app/build/outputs/apk/debug/app-x86-debug.apk
app/build/outputs/apk/debug/app-x86_64-debug.apk
```

## Recommended runtime sequence

### Option A — emulator/no-radio launch first

Use this if the goal is app startup sanity only, with no BLE capability and no MeshCore bridge activation.

Purpose:

- verify APK installs;
- verify main activity launches;
- collect crash/logcat output;
- confirm disabled bridge seams do not crash at startup.

Non-goals:

- BLE behavior;
- mesh discovery;
- message delivery;
- MeshCore bridge traffic;
- stock interoperability.

Preflight commands to run before install:

```bash
adb devices
adb shell getprop ro.build.version.sdk
adb shell getprop ro.product.cpu.abi
```

Install candidate:

- x86_64 emulator: `app-x86_64-debug.apk`
- x86 emulator: `app-x86-debug.apk`
- generic fallback: `app-universal-debug.apk`

Install/run commands, only after explicit approval:

```bash
adb install -r app/build/outputs/apk/debug/app-x86_64-debug.apk
adb shell monkey -p com.bitchat.android 1
adb logcat -c
adb logcat -d -t 500
```

Cleanup command:

```bash
adb uninstall com.bitchat.android
```

### Option B — physical Android device, no bridge activation

Use this only after emulator/no-radio launch or if Eric explicitly wants physical-device install first.

Purpose:

- verify install on real ABI/API;
- observe permission prompts;
- collect launch logs;
- keep all bridge config disabled.

Additional preflight:

```bash
adb devices -l
adb shell getprop ro.product.manufacturer
adb shell getprop ro.product.model
adb shell getprop ro.product.cpu.abi
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk
```

Install candidate by ABI:

- `arm64-v8a`: `app-arm64-v8a-debug.apk`
- `armeabi-v7a`: `app-armeabi-v7a-debug.apk`
- unknown/mixed: `app-universal-debug.apk`

Install/run commands, only after explicit approval:

```bash
adb install -r app/build/outputs/apk/debug/app-arm64-v8a-debug.apk
adb shell monkey -p com.bitchat.android 1
adb logcat -d -t 1000 | grep -i -E 'bitchat|meshbridge|exception|fatal|crash'
```

Cleanup command:

```bash
adb uninstall com.bitchat.android
```

### Option C — physical Android BLE smoke, still no MeshCore bridge activation

This is a later runtime gate, not the first install gate.

Purpose:

- verify app BLE permission flow;
- verify existing bitchat BLE startup behavior is not broken;
- still keep MeshCore bridge config disabled.

Non-goals:

- MeshCore relay;
- app-to-MeshCore traffic;
- MeshCore-to-app traffic;
- stock compatibility claim.

Required approval details before this option:

- exact target device;
- whether nearby Bluetooth devices are allowed to be touched;
- whether BLE advertising/scanning is allowed;
- whether logs can include peer IDs/nicknames;
- rollback command acceptance.

## Bridge config expectations

Current source state:

- inbound `MessageHandler` hook defaults to `DebugMeshBridgePublicTextAdapter()` disabled;
- outbound wrapper defaults to `MeshBridgeDebugAdapterConfiguration.disabled()`;
- no runtime setting enables these paths;
- no injected app sender is configured in production app code;
- `BluetoothMeshService.sendMessage(...)` is not called by bridge code.

Expected runtime result:

- app startup should not emit bridge events;
- bridge-originated outbound text should not be possible;
- normal app behavior should remain unchanged unless the upstream app itself behaves differently.

## Log capture plan

Minimum useful logs after install/run:

```bash
adb logcat -c
adb shell monkey -p com.bitchat.android 1
sleep 10
adb logcat -d -t 1000 > /tmp/bitchat-android-gate5m-logcat.txt
```

Filter:

```bash
grep -i -E 'bitchat|meshbridge|exception|fatal|crash|bluetooth|ble' /tmp/bitchat-android-gate5m-logcat.txt
```

If sending logs back to the user, review/redact:

- peer IDs;
- phone model if sensitive;
- Bluetooth MAC-like identifiers;
- nicknames;
- contact/channel names.

## Hard stop conditions

Stop immediately and do not proceed to BLE/message tests if any occur:

- APK install fails with signing/package errors;
- app crashes on launch;
- permission dialog cannot be safely handled;
- app enables unexpected bridge behavior;
- logcat shows repeated fatal exceptions;
- Eric has not named the target device/emulator.

## Explicit non-claims

Gate 5M does not prove:

- installation;
- launch;
- BLE permissions;
- BLE scan/advertise;
- message delivery;
- MeshCore bridge traffic;
- stock bitchat interoperability;
- production readiness.

It is only the checklist for the next explicit runtime approval gate.

## Approval needed before proceeding

Before install/run, Eric should choose one:

1. emulator/no-radio install + launch only;
2. physical Android install + launch only;
3. physical Android BLE smoke, no bridge activation;
4. stop Android runtime and continue local-only bridge work.

Default safest choice: option 1, emulator/no-radio install + launch only.
