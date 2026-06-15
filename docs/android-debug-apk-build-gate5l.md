# Gate 5L — Android debug APK build preflight

## Status

Completed locally: 2026-06-15 EDT

Gate 5L performed a local Android debug build artifact preflight for the current adapter branch. This confirms the app still compiles/packages after Gates 5G/5I/5J/5K, beyond unit-test compilation. It does **not** install, run, sign for release, distribute, publish, or activate the app on a device/emulator.

## Android local branch

```text
repo: /tmp/bitchat-android
branch: gate5g-android-adapter-stub
base: 13585a9 Automated update of relay data - Sun Jun 14 07:39:17 UTC 2026
Gate 5G: 5592c3f Add disabled Mesh bridge Android adapter stub
Gate 5I: 55f2ae9 Add Mesh bridge public text mapper seam
Gate 5J: eb0a330 Add disabled Mesh bridge Android message hook
Gate 5K: 55ad1b5 Add disabled Mesh bridge outbound wrapper
```

Android git status after build:

```text
## gate5g-android-adapter-stub
```

No source changes were produced by the build.

## Command

```bash
cd /tmp/bitchat-android
export JAVA_HOME=/home/openclaw/.local/android-tooling/jdk-17
export ANDROID_HOME=/home/openclaw/.local/android-sdk
export ANDROID_SDK_ROOT=/home/openclaw/.local/android-sdk
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
./gradlew :app:assembleDebug --no-daemon
```

## Result

```text
BUILD SUCCESSFUL in 2m 37s
33 actionable tasks: 22 executed, 11 up-to-date
```

Generated local debug APK artifacts:

```text
app/build/outputs/apk/debug/app-arm64-v8a-debug.apk      37,844,382 bytes
app/build/outputs/apk/debug/app-armeabi-v7a-debug.apk    34,615,308 bytes
app/build/outputs/apk/debug/app-universal-debug.apk       69,991,022 bytes
app/build/outputs/apk/debug/app-x86-debug.apk             39,727,428 bytes
app/build/outputs/apk/debug/app-x86_64-debug.apk          39,728,543 bytes
```

Gradle warnings observed:

- Gradle deprecated-feature warning for future Gradle 9 compatibility.
- Native debug symbol strip warning for several third-party `.so` libraries; Gradle packaged them as-is.

Neither warning blocked the debug build.

## Explicit non-claims

Gate 5L does not prove:

- app install success;
- app launch success;
- Android runtime behavior;
- BLE permissions/runtime behavior;
- live bridge activation;
- MeshCore hardware path;
- APK release signing;
- public distribution readiness;
- upstream acceptance;
- stock bitchat interoperability.

It proves only that the current local Android branch packages debug APK artifacts successfully.

## Next recommended gate

**Gate 5M — Android runtime/device preflight checklist, then explicit approval before install/run.**

A safe next step is to prepare a runtime checklist for emulator/device testing:

1. target device/emulator selection;
2. Android version/API;
3. BLE permission expectations;
4. whether to use no-radio emulator launch vs physical BLE device;
5. how to keep bridge config disabled;
6. exact install/run/logcat commands;
7. rollback/cleanup commands.

Actual installation or live runtime testing should remain separately approved before execution.
