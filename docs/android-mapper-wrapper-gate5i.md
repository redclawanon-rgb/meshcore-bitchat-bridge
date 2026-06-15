# Gate 5I — Android pure mapper + disabled service wrapper seam

## Status

Completed locally: 2026-06-15 08:45 EDT

Gate 5I added a pure Android public-text mapper and a disabled service-wrapper seam in the local Android checkout. This gate still does **not** wire the adapter into Android BLE, `MessageHandler.handleBroadcastMessage(...)`, `BluetoothMeshService.sendMessage(...)`, mobile runtime, MeshCore hardware, or stock bitchat interoperability.

## Android local branch and commits

```text
repo: /tmp/bitchat-android
branch: gate5g-android-adapter-stub
base: 13585a9 Automated update of relay data - Sun Jun 14 07:39:17 UTC 2026
Gate 5G commit: 5592c3f Add disabled Mesh bridge Android adapter stub
Gate 5I commit: 55f2ae9 Add Mesh bridge public text mapper seam
```

Gate 5I changed:

```text
app/src/main/java/com/bitchat/android/bridge/MeshBridgePublicTextMapper.kt
app/src/test/java/com/bitchat/android/bridge/MeshBridgePublicTextMapperTest.kt
```

## What was added

### `MeshBridgePublicTextMapper`

A pure mapper:

```kotlin
MeshBridgePublicTextMapper.mapAcceptedPublicMessage(
    message: BitchatMessage,
    packetIdHex: String = message.id,
): MeshBridgeVerifiedPublicTextEvent?
```

It emits a Gate 5D-compatible Android event only for accepted plain public text and returns null for messages that should not bridge.

Rejects:

- blank content;
- missing/blank sender peer ID;
- private messages;
- channel messages in this first bridge mode;
- file/media messages;
- blank packet/message IDs.

Emits:

- text;
- sender peer ID;
- timestamp ms;
- packet ID;
- `platform = "android"`;
- `accepted = true`;
- nickname from `message.sender`;
- app message ID from `message.id`.

### `MeshBridgeDebugServiceWrapper`

A debug-only wrapper around `MeshBridgePublicTextAdapter`:

```kotlin
MeshBridgeDebugServiceWrapper.publishBridgePublicText(
    text: String,
    bridgeId: Int,
    messageId: Long,
): MeshBridgePublishResult
```

Important: this wrapper does **not** call `BluetoothMeshService.sendMessage(...)`, BLE APIs, Android lifecycle components, sockets, files, or MeshCore hardware. It only delegates to the already disabled/debug adapter. A future gate can replace the injected debug publisher with an app send-path call after explicit approval.

## Verification

Command:

```bash
cd /tmp/bitchat-android
export JAVA_HOME=/home/openclaw/.local/android-tooling/jdk-17
export ANDROID_HOME=/home/openclaw/.local/android-sdk
export ANDROID_SDK_ROOT=/home/openclaw/.local/android-sdk
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
./gradlew :app:testDebugUnitTest --tests 'com.bitchat.android.bridge.*' --no-daemon
```

Result:

```text
BUILD SUCCESSFUL
TEST-com.bitchat.android.bridge.MeshBridgePublicTextAdapterTest.xml tests=5 failures=0 errors=0 skipped=0
TEST-com.bitchat.android.bridge.MeshBridgePublicTextMapperTest.xml tests=4 failures=0 errors=0 skipped=0
```

## Explicit non-claims

Gate 5I does not prove:

- live Android app integration;
- BLE discovery/advertising;
- `MessageHandler` live hook behavior;
- `BluetoothMeshService.sendMessage(...)` bridge publishing;
- Android service lifecycle behavior;
- mobile background execution;
- app signing/release readiness;
- stock bitchat interoperability;
- production security;
- MeshCore-to-bitchat end-to-end delivery.

It proves only that the pure mapping/wrapper seams compile and are unit-tested.

## Next recommended gate

**Gate 5J — disabled no-op Android hook insertion.**

Recommended next code step:

1. Add a default-disabled adapter holder to the relevant Android service/handler layer.
2. Add a no-op live tap after public-text message construction in `MessageHandler.handleBroadcastMessage(...)`, still disabled by default.
3. Add a debug wrapper method that can be unit-tested but does not send through BLE unless a future gate explicitly enables it.
4. Verify tests still pass.

Gate 5J should still avoid live BLE/device/runtime testing unless Eric explicitly approves that gate.
