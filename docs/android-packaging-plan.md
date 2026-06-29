# Android packaging plan

## Status

Prepared: 2026-06-29 UTC

This plan defines packaging for the first installable Android phone MVP. It does not handle release signing keys, publish an APK, install on a device, or claim app-store readiness.

## First artifact type

The first phone MVP artifact is a **debug APK for sideloading with adb**.

The expected Android build command is:

```bash
./gradlew :app:assembleDebug --no-daemon
```

## APK selection

Use the ABI-specific APK when the target phone ABI is known:

- `app/build/outputs/apk/debug/app-arm64-v8a-debug.apk` for most modern physical Android phones.
- `app/build/outputs/apk/debug/app-armeabi-v7a-debug.apk` for older 32-bit ARM phones.
- `app/build/outputs/apk/debug/app-universal-debug.apk` when ABI is unknown or for fallback debugging.

Do not use x86/x86_64 APKs for a physical ARM phone unless the target device actually reports that ABI.

## Version label

Every phone MVP build report should record:

```text
bridge repo commit
Android repo commit
APK filename
APK SHA-256
build date/time UTC
debug/non-production label
runtime bridge default: disabled
selected transport: fake/local_endpoint/meshcore_ble
```

## Signing scope

Debug signing is acceptable only for the first phone MVP.

Release signing is a later gate and must define:

- keystore ownership;
- password/secret storage outside git;
- rotation/revocation plan;
- versionCode/versionName policy;
- distribution channel;
- privacy/security wording review.

No keystore, signing password, token, or private release credential should be committed, logged, pasted into prompts, or captured in screenshots.

## Distribution scope

Allowed for the first phone MVP:

- local build;
- local SHA-256 hash;
- direct `adb install` to a named test phone after explicit runtime approval.

Not allowed without separate approval:

- public APK upload;
- Play Store or internal app sharing;
- GitHub release artifact;
- upstream PR or fork push;
- TestFlight/App Store release;
- production or user-facing release announcement.
