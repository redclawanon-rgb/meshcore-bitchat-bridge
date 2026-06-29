# Decisions

## D001 — MVP scope

Decision: Start with a text-only bridge-frame tunnel, not stock bitchat compatibility.

Rationale: Proves the MeshCore transport path before taking on bitchat UI, Noise sessions, Nostr, or mobile background constraints.

## D002 — Loop style

Decision: Use repo-centered, issue-per-loop, artifact-first development.

Rationale: Avoids usage-cap failures and preserves continuity across sessions.

## D003 — MVP MeshCore carrier

Decision: Use MeshCore companion channel data datagrams first: companion command `0x3E`, radio-level `PAYLOAD_TYPE_GRP_DATA`, development `data_type = 0xFFFF`.

Rationale: The path is already exposed by MeshCore's companion protocol, carries opaque binary payloads, and avoids invasive firmware protocol changes for the first MVP tunnel. The companion payload limit is 163 bytes, so bridge v0 budgets for a 141-byte fragment body after 22 bytes of bridge overhead.

## D004 — First live adapter path

Decision: Use a transport-neutral companion-datagram seam, implement serial first when hardware is available, then BLE second.

Rationale: The local simulator already proves command/notification bytes. Serial is the lowest-friction first hardware path from a Linux/USB environment and avoids BLE scan/pairing/MTU issues during initial bring-up. BLE remains important for later mobile/bitchat-adjacent integration.

## D005 — bitchat-side MVP seam

Decision: Keep the bitchat-side MVP adapter semantic and text-only: decoded bridge `DeliveredText` enters a future fake/real `BitchatTextCarrier`, and carrier-originated public text exits back into bridge-frame fragmentation. Do not forge stock `BitchatPacket` bytes or claim stock bitchat/BLE compatibility in this repository's MVP.

Rationale: Public bitchat source shows an app-level `Transport` protocol and BLE implementation that construct/sign/encode public `BitchatPacket` values internally before CoreBluetooth writes, then deliver inbound public text as typed transport/delegate events after packet validation. A local semantic seam lets this bridge prove the MeshCore/text handoff without taking ownership of bitchat signatures, Noise sessions, peer identity, BLE fragmentation, app lifecycle, or interoperability claims.

## D006 — post-daemon bitchat adapter path

Decision: After Gate 2H, do scoped upstream-aware bitchat adapter work before any live stock-BLE interoperability attempt. The next technical gate should be version-pinned packet conformance fixtures and tests, not a Python daemon pretending to be a stock bitchat BLE peer.

Rationale: Gate 4 research pinned current iOS and Android upstream sources and found that public text is semantic UTF-8 inside `MESSAGE` packets only after upstream identity, signing, peer verification, dedup, BLE fragmentation/backpressure, and app lifecycle behavior are handled. The iOS app has a useful in-app `Transport` abstraction; Android has clear public send/receive paths but is GPL-3.0. Neither exposes a stable external daemon API. A fixture-first loop can test packet assumptions while preserving the existing no-BLE/no-stock-claim boundary.

## D007 — Gate 4A packet fixture boundary

Decision: The local `bitchat_packet_fixture` module is a research/conformance fixture subset only: raw unpadded v1 public `MESSAGE` packet field encoding/decoding, iOS-style no-recipient and Android-style broadcast-recipient shapes, and structural 64-byte signature length handling. It must not be used as a stock-bitchat BLE adapter or treated as crypto validation.

Rationale: Gate 4A gives deterministic packet bytes for planning and regression tests while preserving the no-BLE/no-stock-compatibility boundary. Padding, compression, fragmentation, signing, signature verification, Noise, peer verification, app lifecycle, and BLE behavior remain separate future gates.

## D008 — Gate 4B padding/compression/preimage fixture boundary

Decision: The local packet fixture module may model observed v1 padding, raw-deflate compression, and signing-preimage shape for deterministic tests, but it still must not sign packets, verify signatures, claim peer authenticity, open BLE, or claim stock bitchat compatibility.

Rationale: Gate 4B mirrors upstream-observed field transformations: PKCS#7-style block padding, raw-deflate compression with original-size prefix, raw-first/unpad decode fallback, and signing preimage construction with TTL fixed to `SYNC_TTL_HOPS = 0` and signature removed. These are necessary conformance facts, but compatibility still depends on real identity keys, signing/verification, Noise sessions, peer registry policy, BLE behavior, and app lifecycle.

## D009 — Gate 4C identity/signature fixture boundary

Decision: The project may use deterministic non-secret Ed25519 fixtures to test upstream-observed signing byte shapes, announce canonical bytes, and identity TLV encoding. These fixtures must not be treated as real device identity, trust establishment, Noise authentication, verified peer registry behavior, BLE interoperability, or stock bitchat compatibility.

Rationale: Gate 4C confirms Ed25519 signing/verification over `toBinaryDataForSigning()` and announce-binding bytes, but real compatibility still depends on persistent device keys, Noise static identity, signed announces accepted by trust policy, peer registry updates, app lifecycle, and BLE transport behavior.

## D010 — Gate 4D verified-sender simulation boundary

Decision: The project may use `VerifiedSenderFixtureRegistry` as a local acceptance-policy fixture: signed identity announces register a peer's signing key, and signed public messages are accepted only after the sender has a verified announce and the public-message signature verifies against the registered key.

Rationale: This ties packet byte shape, Ed25519 signing, identity TLV, and public-message receive gating together in deterministic tests. It remains a local seam simulation only; real interoperability still requires BLE discovery, Noise sessions, app lifecycle, persistence, trust UX/policy edge cases, and mobile peer-registry behavior.

## D011 — Gate 4E v2/route/fragment fixture boundary

Decision: The project may use deterministic local fixtures for v2 route-bearing packets, fragment payload encode/decode/reassembly, and gossip packet IDs. v2 route support is limited to observed byte layout: 4-byte payload length, `HAS_ROUTE = 0x08`, 1-byte route count, and 8-byte route hops before payload.

Rationale: Gate 4E pins the next protocol seam needed before app/live integration: routed v2 frames, fragment packet payloads, and dedup IDs. It remains a fixture-only gate; live relay behavior, BLE stream assembly, route planning, transfer scheduling, Noise/session routing, mobile lifecycle, and stock compatibility are still separate decisions/gates.

## D012 — Gate 5A app-native adapter boundary

Decision: The next bitchat-side integration layer should be an app-native adapter contract, proven locally first with deterministic Gate 4 fixtures. The MeshCore bridge core should consume semantic public-text events and publish bridge-delivered text through an adapter API; it should not directly own BLE, Noise, app lifecycle, route planning, trust UI, or mobile persistence.

Rationale: Gate 5A defines `BitchatAppAdapter` and `LocalFixtureBitchatAppAdapter` as the seam between fixture-proven packet behavior and future Android/iOS integration. This keeps the Python bridge architecture clean while avoiding a false stock-BLE compatibility claim. Live Android/iOS insertion points remain future gates.

## D013 — Gate 5B adapter-backed pump boundary

Decision: The local bridge pump may use the app-native adapter contract through `pump_app_adapter_bridge_once(...)`: MeshCore-delivered text is published to `BitchatAppAdapter.publish_bridge_text(...)`, while fixture-backed app packet bytes are ingested through `BitchatAppAdapter.ingest_packet_bytes(...)` and emitted public-text events are forwarded over the existing MeshCore transport-neutral send path.

Rationale: This connects the Gate 5A app adapter seam to the actual bridge loop while preserving the no-hardware/no-BLE/no-stock-compatibility boundary. The older semantic-carrier pump remains for simpler fake-carrier tests. Android/iOS insertion points are still future design/spike work.

## D014 — Gate 5C app insertion-point mapping

Decision: Future live app work should use app-side semantic public-text adapter surfaces after existing Android/iOS acceptance policy, not raw BLE/BinaryProtocol hooks. Recommended inbound hooks are Android `MessageHandler.handleBroadcastMessage(...)` or service delegate `onMessageReceived(...)`, and iOS `BLEPublicMessageHandlerEnvironment.deliverPublicMessage(...)` or `ChatTransportEventCoordinator.didReceivePublicMessage(...)`. Recommended outbound hooks are Android public `meshService.sendMessage(...)` via a narrow service/API wrapper and iOS `BLEService.sendMessage(..., to: nil, messageID:, timestamp:)` or a UI-level outgoing intent when local echo is desired.

Rationale: Gate 5C inspection found both apps already own BLE decode, fragment reassembly, announce trust, signature policy, public-message acceptance, dedup/sync, route/fragment send behavior, lifecycle, and UI persistence. The bridge should subscribe to verified semantic public text and publish bridge text through existing app send APIs rather than duplicating mobile internals.

## D015 — Gate 5D platform-neutral app adapter API

Decision: The future Android/iOS app adapter contract is a semantic public-text API, not a raw packet/BLE API. App-to-bridge events must be emitted only after app acceptance policy and must carry `text`, `sender_peer_id`, `timestamp_ms`, `packet_id_hex`, `platform`, and explicit `accepted=true`, with optional nickname/app-message/route/source metadata. Bridge-to-app publishing must enter the app's existing public-send path and return an accepted-for-send result that does not claim BLE/radio delivery.

Rationale: Gate 5D makes the Gate 5C insertion-point map implementable without pushing MeshCore concerns into the mobile apps or app internals into the bridge. It also aligns the local Python fixture event with future Android/iOS metadata while preserving no-BLE/no-stock-compatibility boundaries.

## D016 — Gate 5E iOS-first disabled/debug app adapter stub

Decision: The first iOS app-side implementation should be a disabled/debug-only Swift contract/stub, not a live BLEService integration. The local iOS checkout now has `DebugMeshBridgePublicTextAdapter` and focused tests on branch `gate5e-ios-adapter-stub`; it defaults disabled, emits no events, refuses outbound publish with `.adapterDisabled`, and only uses injected closures when explicitly enabled in tests.

Rationale: This validates the Gate 5D contract shape inside iOS without taking ownership of BLE, Noise, signing, route planning, sync, UI persistence, or mobile lifecycle. It creates a safe insertion target for a future debug-only hook while avoiding a premature stock compatibility or radio-delivery claim.

## D017 — Gate 5E iOS debug inbound/outbound hooks

Decision: The iOS adapter path may expose two debug-only hook points before any live bridge transport is connected: `BLEPublicMessageHandlerEnvironment.recordBridgeAcceptedPublicText` for post-acceptance app-to-bridge events, and `BLEService.debugPublishBridgePublicText(...)` for bridge-to-app acceptance into the existing public send path. Both remain unwired by default; the inbound hook defaults no-op and the outbound wrapper is only active if explicitly called.

Rationale: This completes the requested iOS hook seams while preserving app ownership of BLE, packet construction/signing, sync tracking, trust, UI, and persistence. It gives a concrete future wiring point without silently enabling a live bridge, making radio-delivery claims, or bypassing iOS acceptance policy.

## D018 — Gate 5E iOS config owner remains fully disabled by default

Decision: iOS bridge debug wiring now has an explicit local config owner, `MeshBridgeDebugAdapterConfiguration`, whose `.disabled` default turns off inbound event emission and outbound app publication independently. The debug outbound wrapper requires `configuration.outboundPublishEnabled`; compiling the wrapper or calling it without explicit config returns `.adapterDisabled` and sends nothing.

Rationale: With only an old MacBook available for non-Xcode validation, progress should remain source-level and low-risk. A separate fully-off config owner prevents accidental runtime activation while keeping the next integration seam concrete and parser-checkable.

## D019 — Bridge-side iOS debug config fixture is executable evidence, not runtime proof

Decision: The bridge repo now models the iOS debug config and hook behavior in Python via `IOSDebugMeshBridgeAdapterFixture`. This fixture is allowed to execute disabled, inbound-only, outbound-only, fully-enabled, and length-rejection cases as contract evidence, but it does not claim iOS app runtime, Xcode build, BLE, CoreBluetooth, stock bitchat interoperability, or radio delivery.

Rationale: Because Eric's reachable MacBook is limited to macOS 11/Xcode 13.2.1 while the upstream app requires Swift tools 5.9/newer Xcode project support, bridge-side fixture execution is the safest way to keep validating the intended semantics without overstating platform proof.

## D020 — Windows daemon persistence remains explicit live-port gated

Decision: The Windows persistence wrapper uses a Scheduled Task and a PowerShell launcher, but both default to dry-run/no-port mode. A live task must be registered with `-EnableRealPorts`, which passes `-OpenRealPorts` to the launcher and then `--open-real-ports` to the Python daemon.

Rationale: The MeshCore daemon is now useful enough to persist/restart on Eric's Windows desktop, but serial access should remain visible and explicit. The scheduled-task wrapper preserves JSONL event logging, state-file message ID persistence, COM5/COM8 port naming, and restart behavior without silently opening hardware during dry-run validation.

## D021 — Gate 5F Android-first app integration path; defer Mac/Xcode

Decision: Continue app-side integration through an Android-first disabled/debug adapter stub, and save Mac/Xcode-dependent iOS build/runtime work for late project stages or a rented Mac VPS. The next executable app gate is Gate 5G: add a default-disabled Kotlin adapter contract in the local Android checkout, with no BLE/message-path wiring unless separately approved.

Rationale: The iOS Gate 5E source stub exists, but full Xcode verification is blocked by the currently available Mac toolchain. Android has already mapped semantic receive/send insertion points and can likely be compiled/tested in a Linux Android SDK/CI environment after Java/SDK tooling is established. Android-first keeps progress moving while preserving the platform-neutral Gate 5D contract and avoiding premature stock compatibility or mobile BLE claims.

## D022 — Gate 5G Android adapter remains disabled/debug-only

Decision: The Android app-side adapter starts as a disabled/debug-only Kotlin contract in `/tmp/bitchat-android`, not a live BLE or message-path integration. `DebugMeshBridgePublicTextAdapter` defaults to no inbound events and no outbound publish; tests may enable injected closures to prove the semantic event/publish shape only.

Rationale: This mirrors the safe iOS Gate 5E pattern while avoiding Mac/Xcode blockers. It gives Android a compile-tested target for future hooks but does not alter BLE discovery, packet processing, `BluetoothMeshService.sendMessage(...)`, UI state, app lifecycle, signing, release behavior, or stock bitchat compatibility.

## D023 — Gate 5H Android hook path stays mapper/wrapper-first

Decision: The next Android code gate should add pure mapping and disabled wrapper seams before any live hook wiring. Preferred inbound mapping remains post-verification public text in `MessageHandler.handleBroadcastMessage(...)`; preferred outbound route is a narrow debug wrapper around app-owned public send behavior, but default-disabled and test-only until a later gate.

Rationale: Re-inspection confirms Android already owns verification, file/private filtering, public text decode, packet IDs, signing, broadcast, and gossip sync. A mapper/wrapper-first approach keeps BLE/app lifecycle untouched while making future hook wiring small, reversible, and unit-testable.

## D024 — Gate 5I mapper/wrapper seams remain non-live

Decision: Android may now include a pure public-text mapper and disabled debug service wrapper as local seams, but they must remain non-live until a separate hook gate. The mapper can translate accepted `BitchatMessage` public text into `MeshBridgeVerifiedPublicTextEvent`; the wrapper delegates only to the debug adapter and does not call BLE or `BluetoothMeshService.sendMessage(...)`.

Rationale: This gives a compile-tested path toward app integration while preserving the no-BLE/no-runtime/no-stock-claim boundary. It lets future live hook work be a small no-op/default-disabled patch instead of mixing mapping, validation, and runtime wiring in one risky step.

## D025 — Gate 5J Android hook insertion remains disabled by default

Decision: Android may contain a post-acceptance public-text hook in `MessageHandler.handleBroadcastMessage(...)` only if it defaults to a disabled `DebugMeshBridgePublicTextAdapter` and is test-injectable. The hook may map accepted plain public text and call `emitVerifiedPublicText(...)`, but normal app behavior must remain no-op unless a later gate explicitly enables runtime wiring.

Rationale: This creates the smallest reversible inbound app->bridge tap after Android verification/policy while preserving app behavior: no BLE calls, no service sends, no UI setting, no runtime activation, and no stock compatibility claim. Tests prove both default no-op delivery and explicit injected-event behavior.

## D026 — Gate 5K outbound wrapper remains callback-injected and disabled

Decision: Android may include a `MeshBridgeOutboundPublicTextWrapper` for future MeshCore -> app public text, but it must default disabled and require an explicitly injected app sender callback. Gate 5K does not inject or call `BluetoothMeshService.sendMessage(...)`; that remains a separate runtime/app activation gate.

Rationale: The wrapper validates bridge text and metadata before any app send callback and lets tests prove rejection/acceptance behavior without BLE, Android lifecycle, or service runtime side effects. Keeping `sendMessage(...)` uninjected avoids accidentally broadcasting bridge-originated content before device runtime approval.

## D027 — Gate 5L stops at debug APK build artifacts

Decision: Android debug APK packaging may be used as a local compile/package preflight after the disabled adapter gates, but installing/running the APK remains a separate approval gate. Gate 5L records generated debug APK artifacts only; no device/emulator, BLE, release signing, upstream push, or public distribution action is taken.

Rationale: `:app:assembleDebug` catches packaging and manifest/resource issues that unit tests do not, while avoiding runtime side effects. It is the safest final local preflight before device/emulator approval.

## D028 — Gate 5M requires explicit target before Android install/run

Decision: Android runtime testing is now gated on Eric naming the target path: emulator/no-radio launch, physical-device launch, physical BLE smoke, or local-only continuation. The safest default recommendation is emulator/no-radio install + launch only. No APK install/run should happen until the target and scope are explicit.

Rationale: Debug APK packaging is proven, but runtime can touch app permissions, Bluetooth, device identifiers, logs, and possibly nearby radios. A named target and scope keeps this reversible and avoids accidental BLE/message-path activation.

## D029 — Gate 5N runtime must move off this VPS emulator

Decision: Android emulator runtime is not a reliable target on this VPS for Gate 5N because `/dev/kvm` is missing, CPU virtualization flags are not exposed, and software-emulated API 30/35 AVDs failed before APK install/launch. Continue runtime testing on a connected physical Android device or a machine/VM with KVM/hardware virtualization exposed.

Rationale: The VPS can build and package the APK, but Android system services failed during emulator boot, causing PackageInstaller null-pointer failures and `DeadSystemException`. Continuing emulator retries here would be low-value and risks noisy, misleading results.

## D030 — First installable phone target is Android debug APK

Decision: The first real installable cell-phone milestone targets a physical Android phone running a sideloaded debug APK. iOS, release signing, app-store distribution, public APK publishing, and production/user-facing release remain separate later gates.

Rationale: Android has the least blocked path because disabled adapter/hook/wrapper seams and debug APK build evidence already exist, while iOS still depends on a compatible Mac/Xcode environment. A debug APK allows install/runtime evidence without implying production readiness or store distribution.

## D031 — Bridge-enabled phone runtime must be explicit, bounded, and debug-only

Decision: Phone bridge behavior must remain disabled by default and require explicit debug/developer enablement, visible warning text, bounded queues, redacted telemetry, and a selected phone-to-MeshCore transport before any bridge-enabled runtime smoke.

Rationale: A phone install can be mistaken for a user-ready secure messenger. Keeping bridge activation explicit and bounded preserves the public-text-only/lab-only boundary while allowing real runtime progress.

## Pending decisions

- Test hardware: which MeshCore-supported boards.
- MVP security: plaintext lab-only vs bridge-level test encryption.
- Long-term app namespace: register a `data_type` instead of using development `0xFFFF`.
- Whether any later stock-compatible bitchat integration should embed/wrap upstream code, target a version-pinned API, or remain a separate bridge mode.
- Gate 5O runtime target: connected physical Android device or a different KVM-capable emulator host.
