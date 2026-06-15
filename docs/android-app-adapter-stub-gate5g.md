# Gate 5G — Android disabled/debug app adapter stub

## Status

Completed locally: 2026-06-15 08:45 EDT

Gate 5G added a disabled-by-default Android app adapter contract/stub in the local Android checkout. This gate modified only the local Android checkout at `/tmp/bitchat-android`; it did **not** wire BLE, Android service/message paths, mobile runtime, MeshCore hardware, or stock bitchat interoperability.

The Android upstream remote is `https://github.com/permissionlesstech/bitchat-android.git`; changes were preserved on a local branch and were not pushed upstream.

## Android local branch and commit

```text
repo: /tmp/bitchat-android
branch: gate5g-android-adapter-stub
base: 13585a9 Automated update of relay data - Sun Jun 14 07:39:17 UTC 2026
commit: 5592c3f Add disabled Mesh bridge Android adapter stub
```

Changed Android files:

```text
app/src/main/java/com/bitchat/android/bridge/MeshBridgeDebugAdapterConfiguration.kt
app/src/main/java/com/bitchat/android/bridge/MeshBridgePublicTextAdapter.kt
app/src/test/java/com/bitchat/android/bridge/MeshBridgePublicTextAdapterTest.kt
```

## Local Android build tooling established

Because the VPS initially lacked Java/Android build tools, local user-scoped tooling was installed under `~/.local`:

```text
JDK: /home/openclaw/.local/android-tooling/jdk-17
Android SDK: /home/openclaw/.local/android-sdk
```

Installed SDK packages:

```text
build-tools;35.0.0
platform-tools;37.0.0
platforms;android-35
```

The Gradle wrapper downloaded and ran Gradle 8.13.

Use this environment for future Android tasks:

```bash
export JAVA_HOME=/home/openclaw/.local/android-tooling/jdk-17
export ANDROID_HOME=/home/openclaw/.local/android-sdk
export ANDROID_SDK_ROOT=/home/openclaw/.local/android-sdk
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
```

## Adapter behavior

`MeshBridgeDebugAdapterConfiguration` defaults fully disabled:

```kotlin
MeshBridgeDebugAdapterConfiguration.disabled()
```

Default behavior:

- inbound events disabled;
- outbound publish disabled;
- no BLE calls;
- no Android message-path calls;
- no MeshCore daemon or hardware interaction.

`MeshBridgeVerifiedPublicTextEvent` models the Gate 5D event shape for future accepted Android public text:

- `text`
- `senderPeerId`
- `timestampMs`
- `packetIdHex`
- `platform = "android"`
- `accepted = true`
- optional `nickname`
- optional `appMessageId`
- optional `route`

`DebugMeshBridgePublicTextAdapter` can be enabled in tests with injected closures only:

- `inboundEventsEnabled` allows a test handler to receive semantic public-text events.
- `outboundPublishEnabled` allows an injected debug publisher closure to accept bridge text.

This is not a live bridge and does not touch the app's BLE service or message pipeline.

## Verification

### Targeted Gate 5G test

```bash
cd /tmp/bitchat-android
export JAVA_HOME=/home/openclaw/.local/android-tooling/jdk-17
export ANDROID_HOME=/home/openclaw/.local/android-sdk
export ANDROID_SDK_ROOT=/home/openclaw/.local/android-sdk
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
./gradlew :app:testDebugUnitTest --tests 'com.bitchat.android.bridge.MeshBridgePublicTextAdapterTest' --no-daemon
```

Result:

```text
BUILD SUCCESSFUL
```

### Full Android debug unit test task

```bash
./gradlew :app:testDebugUnitTest --no-daemon
```

Result:

```text
BUILD SUCCESSFUL
TEST-com.bitchat.android.bridge.MeshBridgePublicTextAdapterTest.xml tests=5 failures=0 errors=0 skipped=0
```

The Android build produced existing upstream deprecation warnings; no Gate 5G compile/test failure occurred.

## Tests added

`MeshBridgePublicTextAdapterTest` covers:

1. disabled configuration is fully no-op;
2. inbound-only config emits accepted public-text events to an injected handler;
3. outbound-only config publishes through an injected debug publisher only;
4. outbound validation rejects blank text, overlong text, out-of-range bridge IDs, and negative message IDs without publishing;
5. events must represent accepted Android public text.

## Explicit non-claims

Gate 5G does not prove:

- live Android app integration;
- BLE discovery/advertising;
- Android service lifecycle behavior;
- mobile background execution;
- app signing/release readiness;
- stock bitchat interoperability;
- production security;
- MeshCore-to-bitchat end-to-end delivery.

It proves only that a disabled Android adapter contract compiles and has local unit tests.

## Next recommended gate

**Gate 5H — Android debug hook mapping/patch plan.**

Recommended next work is still no-live-BLE:

1. Inspect the exact current Android send/receive functions around:
   - `MessageHandler.handleBroadcastMessage(...)`
   - `BluetoothMeshService.onMessageReceived(...)`
   - `BluetoothMeshService.sendMessage(...)`
2. Draft the smallest future hook patch that would connect the disabled adapter to post-acceptance public-message events and app public-send path.
3. Keep default config disabled and add tests for any hookable wrapper before live runtime/device testing.

Do not wire the adapter into live BLE/message paths, push upstream, sign APKs, or claim stock interoperability without a separate explicit gate.
