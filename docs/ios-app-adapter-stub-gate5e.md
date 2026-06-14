# Gate 5E — iOS-first app adapter stub

## Status

Gate 5E iOS-first is complete as a disabled/debug app-side stub in the local iOS checkout.

This gate did modify the local iOS checkout at `/tmp/bitchat-ios`, but it did **not** wire the adapter into live BLE, CoreBluetooth, `BLEService`, mobile runtime, MeshCore hardware, or stock bitchat interoperability.

The iOS upstream remote is `https://github.com/permissionlesstech/bitchat.git`, so the app change was preserved on a local branch and was not pushed to upstream main.

## iOS local branch and commit

```text
repo: /tmp/bitchat-ios
branch: gate5e-ios-adapter-stub
commit: dfdcd6f Add disabled MeshCore bridge adapter stub
```

Changed iOS files:

```text
bitchat/Services/Bridge/MeshBridgePublicTextAdapter.swift
bitchatTests/Services/MeshBridgePublicTextAdapterTests.swift
```

## What the stub adds

`MeshBridgePublicTextAdapter.swift` defines the Gate 5D platform-neutral contract in Swift:

- `MeshBridgeVerifiedPublicTextEvent`
- `MeshBridgeLocalEchoMode`
- `MeshBridgePublishErrorCode`
- `MeshBridgePublishPublicTextResult`
- `MeshBridgePublicTextAdapter`
- `DebugMeshBridgePublicTextAdapter`

The adapter defaults disabled:

```swift
DebugMeshBridgePublicTextAdapter()
```

Default behavior:

- `isEnabled == false`
- `localEchoMode == .none`
- `recordAcceptedPublicText(...)` emits nothing
- `publishBridgePublicText(...)` returns `.adapterDisabled`
- no BLE/app send path is wired
- no packet is constructed, signed, broadcast, or tracked

Enabled debug behavior is dependency-injected for tests only:

- accepted events can be emitted to an injected handler;
- rejected events (`accepted == false`) are ignored;
- bridge-publication can delegate to an injected closure;
- if enabled without a closure, publication returns `.transportUnavailable` rather than claiming delivery.

## Tests added

`MeshBridgePublicTextAdapterTests.swift` covers:

- event defaults match Gate 5D (`platform = "ios"`, `accepted = true`, `source = "ios-app"`);
- disabled adapter emits no inbound event and refuses outbound publish;
- enabled debug adapter emits accepted events only;
- enabled debug publish delegates to an injected app-send closure and returns its result.

## Verification run

This Linux host does not have Swift/Xcode tooling available:

```text
xcodebuild not available on this host
exit_code=127
```

Static checks on the new Swift files passed:

```text
bitchat/Services/Bridge/MeshBridgePublicTextAdapter.swift: lines=172 bytes=5982 braces={:16 }:16 parens=(:18 ):18
bitchatTests/Services/MeshBridgePublicTextAdapterTests.swift: lines=123 bytes=4389 braces={:9 }:9 parens=(:55 ):55
static_new_swift_checks=ok
```

Local iOS git state after commit:

```text
## gate5e-ios-adapter-stub
dfdcd6f (HEAD -> gate5e-ios-adapter-stub) Add disabled MeshCore bridge adapter stub
```

## Non-claims

Gate 5E does not prove:

- iOS Xcode build/test pass;
- app runtime integration;
- BLE discovery/advertising;
- CoreBluetooth packet send/receive;
- `BLEService` wiring;
- MeshCore bridge runtime connection to iOS;
- stock bitchat interoperability;
- mobile background behavior;
- production security;
- real radio delivery.

It only adds a disabled/debug Swift adapter contract/stub and local tests in the iOS checkout.

## Next options

Recommended next gates:

1. Run the iOS tests on a macOS/Xcode host and fix any compile issues.
2. Add a debug-only integration hook at `BLEPublicMessageHandlerEnvironment.deliverPublicMessage(...)` that remains disabled by default.
3. Add a debug-only outbound wrapper around `BLEService.sendMessage(...)`, still disabled by default.
4. Pause mobile work and harden the Windows daemon/service wrapper first.
