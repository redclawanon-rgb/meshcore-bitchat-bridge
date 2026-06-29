# Phone platform scope

## Status

Prepared: 2026-06-29 UTC

This note narrows the next installable-cell-phone milestone. It is a planning/build-spec artifact only: it does not install an APK, run a phone app, open BLE, open serial ports, modify the Windows daemon, publish a release, or claim stock bitchat interoperability.

## First phone target

The first real installable phone target is an **Android physical-phone debug APK**.

This is the fastest safe target because the project already has:

- Android app insertion-point mapping in `docs/bitchat-app-insertion-points-gate5c.md`.
- A platform-neutral app adapter contract in `docs/APP_ADAPTER_API.md`.
- Android-first planning in `docs/gate5f-android-first-app-integration-plan.md`.
- Disabled Android adapter, mapper, hook, outbound wrapper, and debug APK build evidence in the Gate 5G-5L notes.
- Android runtime preflight and the Gate 5N result showing that this VPS is not a useful emulator host, so the next runtime target should be a physical Android device or a KVM-capable emulator host.

## Deferred platforms

### iOS

The iOS app adapter stub remains valuable, but iOS is not the first installable target.

Before iOS can become an installable target, the project needs a compatible Mac/Xcode environment that can:

1. compile the existing Gate 5E stubs;
2. run the app or tests under a supported toolchain;
3. add an iOS runtime enablement path equivalent to the Android debug path;
4. install on a physical iPhone or TestFlight only after separate approval.

Android success does **not** imply iOS support.

### Release-store distribution

Google Play, TestFlight, App Store, public APK hosting, signed release builds, public forks, and upstream PRs are all separate gates. The phone MVP targets sideloaded/debug installation only.

## Non-claims

The Android phone target does not claim:

- iOS support;
- stock bitchat interoperability;
- private-message relay;
- preservation of bitchat's full privacy/security model;
- production security;
- release signing or app-store readiness;
- unattended background reliability.
