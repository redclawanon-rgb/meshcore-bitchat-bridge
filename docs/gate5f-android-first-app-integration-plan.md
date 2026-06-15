# Gate 5F — Android-first app integration plan

## Status

Created: 2026-06-15 08:20 EDT

Gate 5F is a planning/preflight gate. It does **not** modify Android or iOS app code, open BLE, run mobile apps, open serial ports, change the Windows daemon, or claim stock bitchat interoperability.

Eric approved continuing the app-side integration path and asked to save Mac/Xcode work for last; if Mac/Xcode becomes necessary, he may rent a Mac VPS near the end of the project. This plan therefore chooses an Android-first path and defers iOS/Xcode execution.

## Current bridge baseline

The bridge repo already has:

- Gate 5A app-native adapter seam: `tools/bridge_frame_codec/bitchat_app_adapter.py`.
- Gate 5B adapter-backed no-hardware pump: `pump_app_adapter_bridge_once(...)` in `tools/bridge_frame_codec/bridge_pump.py`.
- Gate 5C Android/iOS insertion-point mapping: `docs/bitchat-app-insertion-points-gate5c.md`.
- Gate 5D platform-neutral adapter API: `docs/APP_ADAPTER_API.md`.
- Gate 5E iOS disabled/debug stub documented in `docs/ios-app-adapter-stub-gate5e.md`, but full Xcode verification is blocked by Eric's older Mac toolchain.

The MeshCore side is also stable enough to leave alone while app integration proceeds: COM5/COM8 are the two USB Companion nodes, the Windows scheduled task daemon is running, watchdogs exist, and COM10 is intentionally the iPhone/Bluetooth MeshCore node rather than a USB Companion daemon port.

## Environment inspection

### Android checkout

Local upstream checkout exists:

```text
/tmp/bitchat-android
branch: main...origin/main
HEAD: 13585a9 Automated update of relay data - Sun Jun 14 07:39:17 UTC 2026
```

Key build files exist:

```text
settings.gradle.kts
build.gradle.kts
app/build.gradle.kts
gradlew
```

Build preflight result on this VPS:

```text
./gradlew --version --no-daemon
ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH.
```

No `java`, `javac`, `gradle`, `kotlinc`, or obvious Android SDK directory was found in the current VPS environment.

### iOS checkout

Local upstream checkout exists:

```text
/tmp/bitchat-ios
branch: gate5e-ios-adapter-stub
```

Gate 5E source stubs were preserved there, but full Xcode/SwiftPM build remains blocked until a newer macOS/Xcode environment exists. Per Eric's instruction, iOS/Mac/Xcode work is deferred until late project stages or until a Mac VPS is available.

## Android-first rationale

Android is the less-blocked next live app path because:

1. It avoids the current Mac/Xcode blocker.
2. The existing Gate 5C mapping already identifies concrete Android receive/send insertion points.
3. A Kotlin disabled/debug adapter can be added and unit-tested before any BLE/runtime wiring.
4. The Android path can preserve the same platform-neutral API from Gate 5D without weakening trust boundaries.
5. Android build tooling can likely be installed or provided in a Linux/container/CI environment, whereas iOS requires a suitable Mac/Xcode environment.

## Gate 5F target

Create an Android-side disabled/debug adapter stub equivalent in spirit to Gate 5E iOS:

- app code compiles when Android build tooling is available;
- adapter is disabled by default;
- no BLE connection, scan, advertise, or packet path is changed;
- no message is relayed unless explicitly enabled in a future gated build;
- adapter exposes semantic public-text event and publish-from-bridge shapes matching `docs/APP_ADAPTER_API.md`;
- tests, if feasible in this environment or later CI, prove disabled/default behavior and payload validation.

## Proposed Android files

Recommended new package:

```text
/tmp/bitchat-android/app/src/main/java/com/bitchat/android/bridge/
```

Recommended files:

```text
MeshBridgePublicTextAdapter.kt
MeshBridgeDebugAdapterConfiguration.kt
```

Optional test path if Android/JVM test setup is usable:

```text
/tmp/bitchat-android/app/src/test/java/com/bitchat/android/bridge/MeshBridgePublicTextAdapterTest.kt
```

## Minimal Kotlin API shape

```kotlin
package com.bitchat.android.bridge

data class MeshBridgeVerifiedPublicTextEvent(
    val text: String,
    val senderPeerId: String,
    val timestampMs: Long,
    val packetIdHex: String,
    val platform: String = "android",
    val accepted: Boolean = true,
    val nickname: String? = null,
    val appMessageId: String? = null,
    val route: List<String>? = null,
)

data class MeshBridgePublishResult(
    val acceptedForSend: Boolean,
    val reason: String,
)

interface MeshBridgePublicTextAdapter {
    fun setVerifiedPublicTextHandler(handler: ((MeshBridgeVerifiedPublicTextEvent) -> Unit)?)
    fun emitVerifiedPublicText(event: MeshBridgeVerifiedPublicTextEvent)
    fun publishBridgePublicText(text: String, bridgeId: Int, messageId: Long): MeshBridgePublishResult
}

class DebugMeshBridgePublicTextAdapter(
    private val configuration: MeshBridgeDebugAdapterConfiguration = MeshBridgeDebugAdapterConfiguration.disabled(),
) : MeshBridgePublicTextAdapter {
    // default disabled; future gates wire this to app send/receive paths only after approval
}
```

## Future Android insertion points

Do **not** wire these during the initial disabled-stub gate unless explicitly approved later.

### Android app -> MeshCore bridge

Preferred future hook:

```text
MessageHandler.handleBroadcastMessage(...)
  after verified-peer enforcement and UTF-8 payload decode
  before/alongside delegate?.onMessageReceived(message)
```

Reason: this is after app-owned BLE decode, packet validation, announce trust, signature-derived identity, fragment reassembly, and public-message policy.

Simpler but lower-fidelity future prototype hook:

```text
BluetoothMeshService.MessageHandlerDelegate.onMessageReceived(message)
```

### MeshCore bridge -> Android app

Preferred future send surface:

```text
BluetoothMeshService.sendMessage(content, mentions = emptyList(), channel = null)
```

or a narrow service wrapper that calls that existing app send path.

Avoid raw BLE/BinaryProtocol injection as the first path.

## Gate 5F steps

### Step 1 — Tooling preflight

Before modifying Android source, establish one of:

1. VPS local Android build tooling:
   - JDK installed;
   - Android SDK available;
   - `./gradlew :app:testDebugUnitTest --no-daemon` or a narrower compile/test task can run.
2. CI/dedicated Linux build host with Android SDK.
3. If neither is available, create source-only Kotlin stubs plus a documented blocked verification result, then defer compile verification until tooling exists.

### Step 2 — Add disabled adapter stub

Add only new bridge package files. Do not touch BLE/message send paths yet.

Expected behavior:

- default config disabled;
- inbound event emission returns/does nothing when disabled;
- outbound publish returns `acceptedForSend=false`, reason `adapter_disabled`;
- text length and blank-text guards exist for future safety;
- no secrets, network endpoints, sockets, BLE calls, serial calls, or MeshCore daemon interactions.

### Step 3 — Add tests where tooling allows

Tests should prove:

- disabled default rejects outbound bridge text;
- disabled default does not emit inbound public text;
- inbound-only config can emit a semantic event to a handler;
- outbound-only/fully-enabled config accepts syntactically valid bridge text into the debug adapter only, without sending to BLE;
- overlong/blank text is rejected consistently.

### Step 4 — Record bridge repo evidence

Update this bridge repo, not just `/tmp/bitchat-android`, with:

- Android branch/commit if a local app commit is made;
- exact build/test command and result;
- explicit non-claims;
- next gate recommendation.

## Stop criteria

Stop and report before proceeding if any of these occur:

- Android build tooling requires large system install, paid service, or credentialed account decision.
- Existing Android app build fails for unrelated upstream reasons.
- A required change would touch BLE lifecycle, permissions, scanning/advertising, packet construction, or message send/receive paths.
- A live Android device/emulator is needed.
- Any public fork push, release, PR, upstream issue/comment, or app signing is needed.
- Any step would modify the running MeshCore Windows daemon or COM5/COM8/COM10 state.

## Explicit non-claims

Gate 5F does not prove:

- live Android app integration;
- live iOS app integration;
- BLE discovery/advertising;
- mobile background execution;
- app signing/release readiness;
- stock bitchat interoperability;
- production security;
- MeshCore-to-bitchat end-to-end delivery.

It only chooses the Android-first path, defers Mac/Xcode work, and defines the next safe disabled-stub gate.

## Next recommended executable gate

**Gate 5G — Android disabled/debug adapter stub.**

If Android build tooling can be established on Linux, implement and test the disabled adapter in `/tmp/bitchat-android`. If tooling is not immediately available, add the source-only stub with a documented verification blocker and defer full compile/test to a Linux Android build environment or CI.
