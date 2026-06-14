# Gate 5E — iOS-first app adapter stub

## Status

Gate 5E iOS-first is complete as a disabled/debug app-side stub in the local iOS checkout.

This gate did modify the local iOS checkout at `/tmp/bitchat-ios`, but it did **not** wire the adapter into live BLE, CoreBluetooth, `BLEService`, mobile runtime, MeshCore hardware, or stock bitchat interoperability.

The iOS upstream remote is `https://github.com/permissionlesstech/bitchat.git`, so the app change was preserved on a local branch and was not pushed to upstream main.

## iOS local branch and commits

```text
repo: /tmp/bitchat-ios
branch: gate5e-ios-adapter-stub
dfdcd6f Add disabled MeshCore bridge adapter stub
72fdf18 Add debug MeshCore bridge hooks
44bb8b0 Make bridge adapter stub parser-compatible
72cb7f4 Add disabled Mesh bridge config owner
```

Changed iOS files:

```text
bitchat/Services/Bridge/MeshBridgePublicTextAdapter.swift
bitchat/Services/Bridge/MeshBridgeDebugAdapterConfiguration.swift
bitchat/Services/Bridge/BLEService+MeshBridgeDebugPublish.swift
bitchat/Services/BLE/BLEPublicMessageHandler.swift
bitchatTests/Services/MeshBridgePublicTextAdapterTests.swift
bitchatTests/Services/BLEPublicMessageHandlerTests.swift
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

## Debug inbound and outbound hooks added

Commit `72fdf18` adds the two requested debug hooks while keeping runtime behavior disabled unless explicitly wired later:

1. Inbound app -> bridge hook:

```text
BLEPublicMessageHandlerEnvironment.recordBridgeAcceptedPublicText
```

- Defaults to no-op.
- Called only after `BLEPublicMessageHandler` accepts the public message, resolves the verified display name, tracks sync when appropriate, decodes UTF-8, computes the packet ID, and resolves self-replay message ID.
- Emits `MeshBridgeVerifiedPublicTextEvent` with `text`, `senderPeerID`, `timestampMs`, `packetIDHex`, `nickname`, and optional `appMessageID`.
- Existing `BLEService.makePublicMessageHandlerEnvironment()` does not wire it, so live app behavior remains unchanged.

2. Outbound bridge -> app wrapper:

```text
BLEService.debugPublishBridgePublicText(...)
```

- Not called or wired by default.
- Checks `InputValidator.Limits.maxMessageLength`.
- Constructs deterministic app message ID `meshbridge-<fromBridgeID>-<messageID>`.
- Calls existing `BLEService.sendMessage(..., to: nil, messageID:, timestamp:)` when explicitly invoked.
- Returns `acceptedForSend=true` only for acceptance into the app send pipeline; it does not claim BLE/radio delivery.

## Disabled config owner added

Commit `72cb7f4` adds:

```text
MeshBridgeDebugAdapterConfiguration
```

Default behavior remains fully off:

```swift
MeshBridgeDebugAdapterConfiguration.disabled
```

- `inboundEventsEnabled == false`
- `outboundPublishEnabled == false`
- `localEchoMode == .none`
- `enablesAnyBridgeBehavior == false`

The config intentionally separates inbound and outbound behavior. `DebugMeshBridgePublicTextAdapter` now emits inbound events only when `configuration.inboundEventsEnabled` is true, and publishes bridge text only when `configuration.outboundPublishEnabled` is true. `BLEService.debugPublishBridgePublicText(...)` also takes a `configuration` parameter defaulting to `.disabled`, so merely compiling or accidentally calling the wrapper without explicit config still returns `.adapterDisabled` and sends nothing.

This is not a runtime settings source yet; a later gate can decide whether a debug UI, launch argument, developer default, or test injection owns these values.

## Bridge-side executable config fixture added

The bridge repo now includes a fixture-only executable model of the iOS debug config and hook behavior:

```text
tools/bridge_frame_codec/ios_debug_adapter_fixture.py
tests/test_ios_debug_adapter_fixture.py
```

It mirrors the Swift safety rules without pretending to be an iOS runtime:

- disabled config emits no inbound events and refuses outbound publish with `adapter_disabled`;
- inbound-only config emits accepted iOS public-text events and rejects unaccepted events, but still refuses outbound publish;
- outbound-only config publishes through the existing semantic fake app carrier, creates deterministic `meshbridge-<fromBridgeID>-<messageID>` app IDs, and emits no inbound events;
- fully-enabled config preserves local echo mode and allows both directions;
- outbound length rejection does not publish to the fake app carrier.

## Tests added/updated

`MeshBridgePublicTextAdapterTests.swift` covers:

- event defaults match Gate 5D (`platform = "ios"`, `accepted = true`, `source = "ios-app"`);
- disabled adapter emits no inbound event and refuses outbound publish;
- enabled debug adapter emits accepted events only;
- enabled debug publish delegates to an injected app-send closure and returns its result;
- config owner defaults fully disabled and can enable inbound without enabling outbound publish.

`BLEPublicMessageHandlerTests.swift` now also verifies:

- accepted verified public messages produce a bridge event through `recordBridgeAcceptedPublicText`;
- rejected/self/stale cases leave bridge events empty via the existing no-side-effects helper.

`test_ios_debug_adapter_fixture.py` verifies the executable bridge-side config simulation:

- disabled config is fully no-op;
- inbound-only config emits only accepted events and refuses outbound;
- outbound-only config publishes via the fake app carrier and emits no inbound;
- fully-enabled config supports both directions and preserves local echo mode;
- over-length outbound text is rejected without fake app publication.

## Verification run

This Linux host does not have Swift/Xcode tooling available:

```text
xcodebuild not available on this host
exit_code=127
```

MacBook SSH/Xcode verification was attempted on `Erics-MBP` (`ericdecker`, macOS 11.7.11):

```text
/Applications/Xcode.app/Contents/Developer
Xcode 13.2.1
Build version 13C100
```

Full project build/test is blocked on that Mac because the checked-out project/package require a newer Apple toolchain than macOS 11/Xcode 13 provides:

```text
xcodebuild -list -project bitchat.xcodeproj
xcodebuild: error: Unable to read project 'bitchat.xcodeproj'.
Reason: The project ‘bitchat’ is damaged and cannot be opened.
Exception: didn't find classname for 'isa' key

swift package describe
error: package at '/Users/ericdecker/Developer/bitchat-ios-gate5e' is using Swift tools version 5.9.0 but the installed version is 5.5.0
```

The Gate 5E app source files were staged on the MacBook at `/Users/ericdecker/Developer/bitchat-ios-gate5e`, and direct parser checks for the modified app source files pass under the installed Swift 5.5.2 parser after commit `72cb7f4`:

```text
xcrun swiftc -parse bitchat/Services/Bridge/MeshBridgeDebugAdapterConfiguration.swift
xcrun swiftc -parse bitchat/Services/Bridge/MeshBridgePublicTextAdapter.swift
xcrun swiftc -parse bitchat/Services/Bridge/BLEService+MeshBridgeDebugPublish.swift
xcrun swiftc -parse bitchat/Services/BLE/BLEPublicMessageHandler.swift
mac_gate5e_config_parse_shape_checks=ok
```

Test files still cannot be run under this toolchain because upstream tests use newer Swift Testing syntax (`#expect`).

Static checks on the modified Swift files passed:

```text
bitchat/Services/Bridge/MeshBridgePublicTextAdapter.swift: lines=172 bytes=5982 braces={:16 }:16 parens=(:18 ):18
bitchat/Services/Bridge/BLEService+MeshBridgeDebugPublish.swift: lines=48 bytes=1629 braces={:4 }:4 parens=(:10 ):10
bitchat/Services/BLE/BLEPublicMessageHandler.swift: lines=119 bytes=5199 braces={:10 }:10 parens=(:58 ):58
bitchatTests/Services/MeshBridgePublicTextAdapterTests.swift: lines=123 bytes=4389 braces={:9 }:9 parens=(:55 ):55
bitchatTests/Services/BLEPublicMessageHandlerTests.swift: lines=264 bytes=10755 braces={:26 }:26 parens=(:146 ):146
static_modified_swift_checks=ok
```

Local iOS git state after commit:

```text
## gate5e-ios-adapter-stub
72cb7f4 (HEAD -> gate5e-ios-adapter-stub) Add disabled Mesh bridge config owner
44bb8b0 Make bridge adapter stub parser-compatible
72fdf18 Add debug MeshCore bridge hooks
dfdcd6f Add disabled MeshCore bridge adapter stub
```

## Non-claims

Gate 5E does not prove:

- iOS Xcode build/test pass;
- app runtime integration;
- BLE discovery/advertising;
- CoreBluetooth packet send/receive;
- live `BLEService` adapter wiring;
- MeshCore bridge runtime connection to iOS;
- stock bitchat interoperability;
- mobile background behavior;
- production security;
- real radio delivery.

It only adds a disabled/debug Swift adapter contract/stub and local tests in the iOS checkout.

## Next options

Recommended next gates:

1. Run the iOS tests on a macOS/Xcode host and fix any compile issues.
2. Add an explicit disabled debug flag/config owner for the iOS adapter wiring path.
3. Connect the debug adapter to a real bridge transport process only after a macOS/Xcode pass and explicit live app/BLE approval.
4. Pause mobile work and harden the Windows daemon/service wrapper first.
