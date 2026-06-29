# Android phone security boundary

## Status

Prepared: 2026-06-29 UTC

This document records the security and UX boundary for the Android phone MVP. It is not a security design completion and does not claim production readiness.

## Required debug warning

When bridge behavior can be enabled in an Android debug build, the app should show a warning equivalent to:

> MeshCore bridge is experimental. It relays public text only. It does not preserve bitchat's full privacy/security model, does not support private DMs, and is not production secure.

The warning should appear before enabling bridge behavior and should be visible in any debug settings/status surface while enabled.

## Current security posture

- Bridge frame v0 uses CRC for accidental corruption detection, not adversarial integrity.
- The MVP bridge payload is public text only.
- Private messages, DMs, files, images, Nostr relay, and full Noise tunnel behavior are out of scope.
- App-to-bridge events must come after the app's own public-message acceptance policy.
- Bridge-to-app text must enter the app's existing public-send path, not raw packet/BLE injection.
- Logs should avoid message content by default and must redact sensitive identifiers in reports.

## Debug enablement requirements

Bridge behavior should remain disabled unless all are true:

1. the build is a debug/developer build;
2. the operator explicitly enables the bridge;
3. a transport is explicitly configured;
4. the warning has been acknowledged;
5. queue limits and logging mode are visible to the operator.

## Logs and evidence

Default logs may include:

- event type;
- success/failure status;
- redacted transport name;
- byte counts;
- latency buckets;
- queue depth;
- rejection reason.

Default logs should not include:

- raw private keys or tokens;
- private messages;
- public message text unless explicitly enabled for a small debug smoke;
- full peer IDs;
- nicknames;
- Bluetooth MAC-like identifiers;
- phone serials or unique hardware identifiers.

## Required future security work before public/user release

Before any broader release or production/security claim, the project needs:

- adversarial integrity/authentication for bridge frames or a documented secure tunnel;
- replay protection and freshness rules;
- key management and trust UX;
- privacy review for metadata leakage over MeshCore/LoRa;
- abuse/spam/rate-limit behavior;
- crash/log redaction review;
- background execution and notification privacy review;
- independent review of any public security wording.
