# Gate 5N — Android runtime attempt results

## Status

Attempted: 2026-06-15 14:12 UTC

Eric approved Gate 5N options 1-3:

1. emulator/no-radio install + launch only;
2. physical Android install + launch only;
3. physical Android BLE smoke, still no bridge activation.

Gate 5N did **not** reach APK install or app launch. The VPS can build Android APKs, but Android Emulator runtime is not usable enough on this host because `/dev/kvm` is unavailable and CPU virtualization flags are not exposed. No physical Android device was connected.

## Secret handling

Eric supplied a sudo password through Password Pusher. The secret page was opened, the secret was used for package installation, and the Password Pusher link was deleted after retrieval. The password is not recorded in this repository.

## System dependency install

System packages installed via sudo to satisfy emulator GUI/runtime library dependencies:

```text
libpulse0
libnss3
libxcomposite1
libxcursor1
libxi6
libxtst6
libxrandr2
libasound2t64
libatk1.0-0t64
libatk-bridge2.0-0t64
libcups2t64
libxdamage1
libgbm1
libxkbcommon0
libdrm2
libxcb-cursor0
```

`apt-get update` and `apt-get install` completed successfully.

## Emulator setup completed

Installed Android emulator components:

```text
emulator
platforms;android-30
system-images;android-30;google_apis;x86_64
system-images;android-35;google_apis;x86_64
```

Created AVDs:

```text
gate5n_api30
gate5n_api35
```

Emulator binary now starts far enough to report version:

```text
Android emulator version 36.6.11.0
```

## Runtime environment blocker

Host checks:

```text
/dev/kvm: missing
CPU virtualization flags: none exposed by /proc/cpuinfo
```

Because KVM is unavailable, emulator runs with software translation only (`-accel off`). Both emulator attempts became unstable before APK install/launch could complete.

## API 35 no-radio emulator attempt

Command shape:

```bash
emulator -avd gate5n_api35 \
  -no-window -no-audio -no-boot-anim -accel off \
  -no-snapshot -wipe-data -gpu swiftshader_indirect -memory 2048
```

Observed:

- device eventually appeared as `emulator-5554 device`;
- `sys.boot_completed` never became `1`;
- package service was intermittently unavailable or not fully initialized;
- APK install failed before launch.

Install failure:

```text
adb: failed to install app-x86_64-debug.apk
java.lang.NullPointerException: Attempt to invoke virtual method
'void android.content.pm.PackageManagerInternal.freeStorage(java.lang.String, long, int)'
on a null object reference
```

## API 30 no-radio emulator attempt

Command shape:

```bash
emulator -avd gate5n_api30 \
  -no-window -no-audio -no-boot-anim -accel off \
  -no-snapshot -wipe-data -gpu off -memory 1536
```

Observed:

- device appeared as `emulator-5554 device`;
- `cmd package list packages` eventually returned success once, but system boot still did not complete;
- APK install failed before launch;
- later shell input reported `DeadSystemException`, indicating the Android system server was dead/unusable.

Install failure:

```text
adb: failed to install app-x86_64-debug.apk
java.lang.NullPointerException: Attempt to invoke virtual method
'java.util.List android.os.storage.StorageManager.getVolumes()'
on a null object reference
```

Runtime health after failure:

```text
sys.boot_completed=
dev.bootcomplete=
init.svc.bootanim=stopped
cmd: Can't find service: package
java.lang.RuntimeException: android.os.DeadSystemException
```

Relevant logcat evidence included:

```text
SystemServer: BOOT FAILURE starting StorageStatsService
java.lang.RuntimeException: Failed to start service com.android.server.usage.StorageStatsService$Lifecycle
Caused by: java.lang.NullPointerException
```

## Physical device status

No physical Android device was connected or authorized:

```text
adb devices -l
List of devices attached
```

Therefore Gate 5N options 2 and 3 could not run.

## What did not happen

Gate 5N did not:

- install the APK;
- launch the app;
- interact with a physical device;
- test BLE permissions;
- start BLE scanning/advertising;
- enable bridge relay;
- send or receive MeshCore/app messages;
- claim stock bitchat interoperability.

## Current conclusion

The Android code remains buildable and packaged from Gate 5L, but this VPS is not a reliable Android runtime host because KVM is unavailable. The next runtime step should move to a physical Android device or another machine/VM with hardware virtualization exposed.

## Next recommended gate

**Gate 5O — physical Android install/launch on a connected device**, still no bridge activation.

Requirements:

1. Connect Android device via USB or make it available via `adb connect`.
2. Ensure `adb devices -l` shows `device`, not `unauthorized`.
3. Select ABI-specific APK, likely `app-arm64-v8a-debug.apk` for most modern phones.
4. Install with `adb install -r`.
5. Launch with `adb shell monkey -p com.bitchat.android 1`.
6. Capture filtered logcat.
7. Stop before BLE smoke if launch crashes or permissions are unclear.

If a different machine with working `/dev/kvm` is available, emulator/no-radio testing can also resume there.
