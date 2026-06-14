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

## Pending decisions

- Test hardware: which MeshCore-supported boards.
- MVP security: plaintext lab-only vs bridge-level test encryption.
- Long-term app namespace: register a `data_type` instead of using development `0xFFFF`.
- Whether any later stock-compatible bitchat integration should embed/wrap upstream code, target a version-pinned API, or remain a separate bridge mode.
