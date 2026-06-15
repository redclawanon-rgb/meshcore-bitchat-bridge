# Gate 5J — Android default-disabled no-op message hook

## Status

Completed locally: 2026-06-15 08:45 EDT

Gate 5J inserted a default-disabled no-op Android message hook in the local Android checkout. This is still not live bridge activation: no BLE settings, app UI settings, runtime device/emulator testing, MeshCore hardware, app signing, upstream push, or stock compatibility claim was added.

## Android local branch and commits

```text
repo: /tmp/bitchat-android
branch: gate5g-android-adapter-stub
base: 13585a9 Automated update of relay data - Sun Jun 14 07:39:17 UTC 2026
Gate 5G: 5592c3f Add disabled Mesh bridge Android adapter stub
Gate 5I: 55f2ae9 Add Mesh bridge public text mapper seam
Gate 5J: eb0a330 Add disabled Mesh bridge Android message hook
```

Gate 5J changed:

```text
app/src/main/java/com/bitchat/android/mesh/MessageHandler.kt
app/src/test/java/com/bitchat/android/mesh/MessageHandlerMeshBridgeHookTest.kt
```

## What changed

`MessageHandler` now owns a default-disabled adapter:

```kotlin
private var meshBridgePublicTextAdapter: MeshBridgePublicTextAdapter = DebugMeshBridgePublicTextAdapter()
```

A test-only injection method exists:

```kotlin
internal fun setDebugMeshBridgePublicTextAdapterForTesting(adapter: MeshBridgePublicTextAdapter?)
```

The public broadcast text path now maps accepted plain public text and asks the adapter to emit the event:

```kotlin
MeshBridgePublicTextMapper.mapAcceptedPublicMessage(message)?.let { event ->
    meshBridgePublicTextAdapter.emitVerifiedPublicText(event)
}
delegate?.onMessageReceived(message)
```

Because the default adapter is `DebugMeshBridgePublicTextAdapter()` with all config disabled, this is a no-op in normal app code.

## Why this is still safe

The hook is after Android app policy has accepted the broadcast public text:

- `handleMessage(...)` already ignores self packets.
- `handleBroadcastMessage(...)` has already rejected unverified/unknown peers.
- File-transfer payloads return before this hook.
- Private messages are handled elsewhere.
- The mapper also rejects private/channel/file/blank/missing-peer cases.

The hook does not:

- call BLE APIs;
- call `BluetoothMeshService.sendMessage(...)`;
- send a packet;
- open a socket/file/serial port;
- start a service;
- change app settings;
- alter UI state;
- enable MeshCore relay.

## Verification

Targeted hook test:

```bash
./gradlew :app:testDebugUnitTest --tests 'com.bitchat.android.mesh.MessageHandlerMeshBridgeHookTest' --no-daemon
```

Result:

```text
BUILD SUCCESSFUL
```

Full Android debug unit test task:

```bash
./gradlew :app:testDebugUnitTest --no-daemon
```

Result:

```text
BUILD SUCCESSFUL
TEST-com.bitchat.android.bridge.MeshBridgePublicTextAdapterTest.xml tests=5 failures=0 errors=0 skipped=0
TEST-com.bitchat.android.bridge.MeshBridgePublicTextMapperTest.xml tests=4 failures=0 errors=0 skipped=0
TEST-com.bitchat.android.mesh.MessageHandlerMeshBridgeHookTest.xml tests=2 failures=0 errors=0 skipped=0
```

## Tests added

`MessageHandlerMeshBridgeHookTest` proves:

1. default disabled hook remains a no-op and still delivers the normal app message to the delegate;
2. explicitly injected test adapter can receive the mapped bridge event after verified broadcast public text handling.

## Explicit non-claims

Gate 5J does not prove:

- live Android app/device behavior;
- BLE discovery/advertising;
- MeshCore bridge transport into Android;
- bridge text being sent through `BluetoothMeshService.sendMessage(...)`;
- mobile background execution;
- app signing/release readiness;
- stock bitchat interoperability;
- production security;
- MeshCore-to-bitchat end-to-end delivery.

It proves only that a default-disabled no-op hook compiles and is unit-tested.

## Next recommended gate

**Gate 5K — outbound debug wrapper insertion plan or app-runtime gate.**

At this point, the inbound app -> bridge event tap exists but is disabled unless explicitly injected in tests. The next safe choice is either:

1. add a similarly default-disabled outbound wrapper around `BluetoothMeshService.sendMessage(...)` with tests but no runtime enablement; or
2. stop and require explicit approval for Android device/emulator runtime testing before any actual live app bridge activation.

Do not enable live BLE/message relay, publish an APK, push upstream, or claim stock interoperability without a separate explicit approval gate.
