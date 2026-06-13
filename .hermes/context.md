# MeshCore ↔ bitchat Bridge Context

## Purpose

Build an MVP bridge that can carry bitchat-like text messages over MeshCore/LoRa using a custom bridge-frame tunnel.

## Project root

`/home/openclaw/projects/meshcore-bitchat-bridge`

## Current source of truth

- `README.md` — project overview
- `DESIGN.md` — architecture approach
- `PROTOCOL.md` — bridge frame draft
- `THREAT_MODEL.md` — security posture
- `LOOPS.md` — development loop protocol
- `STATUS.md` — current state and next action
- `DECISIONS.md` — decisions and pending gates

## Current MVP scope

In scope:

- MeshCore custom/group payload tunnel
- tiny bridge-frame protocol
- codec and fragmentation tests
- Python bridge harness
- two-node text demo

Out of scope for MVP:

- full stock bitchat compatibility
- private DMs
- Noise tunneling
- Nostr
- images/files
- production security claims

## Approval boundaries

Do not push public repos, post publicly, or claim production security without Eric's approval.
Do not handle raw secrets in project files.

## Next action

Run MVP-02: inspect MeshCore packet/payload/companion docs and write `evidence/meshcore-payload-budget.md`.
