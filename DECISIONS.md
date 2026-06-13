# Decisions

## D001 — MVP scope

Decision: Start with a text-only bridge-frame tunnel, not stock bitchat compatibility.

Rationale: Proves the MeshCore transport path before taking on bitchat UI, Noise sessions, Nostr, or mobile background constraints.

## D002 — Loop style

Decision: Use repo-centered, issue-per-loop, artifact-first development.

Rationale: Avoids usage-cap failures and preserves continuity across sessions.

## Pending decisions

- Carrier payload: `RAW_CUSTOM` vs `GRP_DATA` vs new payload type.
- Client interface: serial first, BLE first, or both.
- Test hardware: which MeshCore-supported boards.
- MVP security: plaintext lab-only vs bridge-level test encryption.
