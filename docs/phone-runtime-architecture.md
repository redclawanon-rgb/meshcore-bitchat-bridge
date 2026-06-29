# Phone runtime architecture

## Status

Prepared: 2026-06-29 UTC

This document defines the first installable-cell-phone architecture for the MeshCore ↔ bitchat bridge. It is a build specification only: it does not install or run an app, open BLE, open serial ports, transmit LoRa traffic, or make production/security claims.

## Selected first architecture

The first installable phone milestone uses this architecture:

```text
Android bitchat debug APK
  ↕ semantic public-text adapter, disabled by default
Android debug bridge runtime switch
  ↕ explicit bridge transport client
Existing MeshCore bridge service/daemon or direct MeshCore transport, selected by a later transport gate
  ↕ MeshCore companion channel-data datagrams
MeshCore / LoRa nodes
```

The first runtime gate should prove the Android APK installs and launches with bridge behavior disabled. The next bridge-enabled gate should use a fake or local explicit transport before any live BLE or LoRa behavior is enabled.

## Runtime ownership boundaries

### Android app owns

- Existing bitchat BLE lifecycle and permissions.
- Public-message verification/acceptance before emitting app-to-bridge events.
- Existing public-send API for bridge-to-app publication.
- Debug-only bridge enablement UX and warning text.
- Local validation before accepting bridge-originated text.

### Bridge transport owns

- MeshCore companion channel-data framing.
- Bridge-frame fragmentation/reassembly.
- Queueing, timeout, duplicate handling, and telemetry.
- Connection details for either a local bridge endpoint or direct MeshCore companion transport.

### MeshCore nodes own

- RF settings, channel behavior, LoRa delivery, and companion-protocol behavior.

## Candidate phone-to-MeshCore transport choices

The exact first live transport remains a gate decision. Only one should be selected for the first bridge-enabled phone smoke.

### Option A — Android app talks to an explicit local bridge endpoint

The existing Python/Windows MeshCore daemon exposes a small local endpoint, and the Android debug APK connects to a configured host/port.

Pros:

- Reuses the proven COM5/COM8 MeshCore USB Companion path.
- Avoids combining bitchat BLE and MeshCore BLE in one first phone gate.
- Keeps LoRa/MeshCore transport logic mostly in the existing bridge repo.

Cons:

- Requires a companion PC or service.
- Adds local-network configuration and security concerns.
- Is not phone-standalone.

### Option B — Android app talks directly to MeshCore BLE Companion

The Android debug APK discovers/connects to a known MeshCore BLE Companion endpoint and sends bridge datagrams directly.

Pros:

- Moves toward a standalone phone install.
- Avoids an external bridge service.

Cons:

- Requires careful BLE permission/lifecycle work.
- Risks interacting with nearby radios if not tightly scoped.
- May compete with existing bitchat BLE behavior and battery budget.

## Recommended sequence

1. Install-only physical Android debug APK, bridge disabled.
2. Debug runtime enable switch with fake/local in-process transport.
3. Pick Option A or Option B for the first live bridge-enabled transport.
4. Add bounded queueing, telemetry, and redacted logs before live transport.
5. Run one-phone bridge-enabled smoke.
6. Run two-endpoint field smoke only after one-phone smoke passes.

## Stop criteria

Stop before continuing if:

- the APK crashes on launch;
- bridge behavior activates while disabled;
- a transport needs broad BLE scan/connect permissions not explicitly approved;
- private messages or non-public channels are reachable by the bridge;
- logs expose raw secrets, private message content, unredacted peer identifiers, or phone identifiers;
- the selected transport would imply production security or stock interoperability claims.
