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

## Pending decisions

- Test hardware: which MeshCore-supported boards.
- MVP security: plaintext lab-only vs bridge-level test encryption.
- Long-term app namespace: register a `data_type` instead of using development `0xFFFF`.
- Whether any later stock-compatible bitchat integration should embed/wrap upstream code, target a version-pinned API, or remain a separate bridge mode.
