# Gate 5K — Android default-disabled outbound wrapper

## Status

Completed locally: 2026-06-15 EDT

Gate 5K added a default-disabled outbound wrapper seam for a future MeshCore -> Android public text send path. This gate intentionally does **not** wire the wrapper into `BluetoothMeshService.sendMessage(...)`, BLE, Android lifecycle/runtime settings, MeshCore hardware, an APK, upstream Android repo, or stock bitchat interoperability.

## Android local branch and commits

```text
repo: /tmp/bitchat-android
branch: gate5g-android-adapter-stub
base: 13585a9 Automated update of relay data - Sun Jun 14 07:39:17 UTC 2026
Gate 5G: 5592c3f Add disabled Mesh bridge Android adapter stub
Gate 5I: 55f2ae9 Add Mesh bridge public text mapper seam
Gate 5J: eb0a330 Add disabled Mesh bridge Android message hook
Gate 5K: 55ad1b5 Add disabled Mesh bridge outbound wrapper
```

Gate 5K changed:

```text
app/src/main/java/com/bitchat/android/bridge/MeshBridgeOutboundPublicTextWrapper.kt
app/src/test/java/com/bitchat/android/bridge/MeshBridgeOutboundPublicTextWrapperTest.kt
```

## Outbound path inspected

Current Android public send path remains:

```kotlin
BluetoothMeshService.sendMessage(content: String, mentions: List<String> = emptyList(), channel: String? = null)
```

Observed behavior in current source:

1. rejects empty content;
2. launches on `serviceScope`;
3. builds a `BitchatPacket` with `MessageType.MESSAGE`, `SpecialRecipients.BROADCAST`, and UTF-8 payload;
4. signs with `signPacketBeforeBroadcast(packet)`;
5. broadcasts through `connectionManager.broadcastPacket(RoutedPacket(signedPacket))`;
6. records the public packet with `gossipSyncManager.onPublicPacketSeen(signedPacket)`.

Gate 5K does not call this method directly. It creates a safe wrapper where a later explicit runtime gate can inject `BluetoothMeshService::sendMessage` after approval.

## What was added

`MeshBridgeOutboundPublicTextWrapper`:

```kotlin
class MeshBridgeOutboundPublicTextWrapper(
    private val configuration: MeshBridgeDebugAdapterConfiguration = MeshBridgeDebugAdapterConfiguration.disabled(),
    private val appPublicTextSender: ((String) -> Unit)? = null,
)
```

Main method:

```kotlin
fun publishBridgePublicText(
    text: String,
    bridgeId: Int,
    messageId: Long,
): MeshBridgePublishResult
```

Behavior:

- default config rejects with `outbound_wrapper_disabled`;
- validates blank text, over-length text, bridge ID range, and message ID range before any send callback;
- rejects with `app_sender_missing` when enabled but no app sender is injected;
- only calls the injected sender when explicitly enabled and valid.

## Verification

Targeted wrapper test:

```bash
./gradlew :app:testDebugUnitTest --tests 'com.bitchat.android.bridge.MeshBridgeOutboundPublicTextWrapperTest' --no-daemon
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
TEST-com.bitchat.android.bridge.MeshBridgeOutboundPublicTextWrapperTest.xml tests=4 failures=0 errors=0 skipped=0
TEST-com.bitchat.android.bridge.MeshBridgePublicTextAdapterTest.xml tests=5 failures=0 errors=0 skipped=0
TEST-com.bitchat.android.bridge.MeshBridgePublicTextMapperTest.xml tests=4 failures=0 errors=0 skipped=0
TEST-com.bitchat.android.mesh.MessageHandlerMeshBridgeHookTest.xml tests=2 failures=0 errors=0 skipped=0
```

## Explicit non-claims

Gate 5K does not prove:

- live Android app/device behavior;
- BLE discovery/advertising;
- Android service runtime behavior;
- bridge messages being sent through `BluetoothMeshService.sendMessage(...)`;
- mobile background behavior;
- app signing/release readiness;
- stock bitchat interoperability;
- production security;
- MeshCore-to-bitchat end-to-end delivery.

It proves only that a default-disabled outbound seam compiles and is unit-tested.

## Next recommended gate

**Gate 5L — Android runtime preflight plan/checklist or local unit-only service holder.**

The remaining local-only coding surface is now thin. The next meaningful step is either:

1. add a no-op service-level holder for the outbound wrapper with default disabled config and tests, still not calling `sendMessage(...)`; or
2. stop and require explicit approval for Android emulator/device runtime testing before any actual live app bridge activation.

Do not enable live BLE/message relay, publish an APK, push upstream, or claim stock interoperability without a separate explicit approval gate.
