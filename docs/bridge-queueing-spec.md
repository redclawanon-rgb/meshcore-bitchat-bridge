# Bridge queueing and failure behavior spec

## Status

Prepared: 2026-06-29 UTC

This spec defines queueing/failure behavior required before bridge-enabled phone runtime testing. It does not implement queueing, open transports, transmit LoRa packets, or claim reliable delivery.

## Goals

- Prevent phone UI or app hooks from overwhelming LoRa/MeshCore transport.
- Bound memory usage and retries.
- Make failure states visible in debug telemetry.
- Avoid duplicate public-text relay.
- Keep disabled/default behavior safe.

## Queues

A phone runtime should maintain bounded queues for:

1. app-to-MeshCore public text events;
2. MeshCore-to-app public text events;
3. transport retry/deferred-send items, if the selected transport needs them.

Recommended first limits:

```text
max_app_to_meshcore_pending = 16
max_meshcore_to_app_pending = 16
max_payload_bytes_per_text = bridge/app adapter limit, whichever is smaller
max_retry_attempts = 2 for debug smoke
message_timeout_seconds = 60 for debug smoke
```

These are initial debug values, not production tuning.

## Queue-full behavior

The first phone MVP should reject the newest item when a queue is full.

Rationale: rejecting newest with a visible reason is easier to reason about than silently dropping older pending text that may already have UI status.

Required rejection result fields:

```text
accepted = false
reason = queue_full
direction = app_to_meshcore | meshcore_to_app
queue_depth
max_queue_depth
```

## Duplicate suppression

Duplicate suppression should use all identifiers available for the direction:

- bridge-to-app: `(bridge_id, message_id, msg_type)` plus packet ID if available;
- app-to-bridge: app packet ID/event ID plus sender peer ID and timestamp where available;
- transport-level retransmit: bridge frame fragment identity.

Duplicate entries should be counted and dropped without re-publishing.

## Timeout and retry

For the debug MVP:

- retry at most twice for transient transport failure;
- stop retrying after `message_timeout_seconds`;
- emit a debug failure event with redacted identifiers;
- do not block the app UI thread while waiting for MeshCore/LoRa delivery.

ACK/NACK frame support remains a future protocol gate unless live measurements justify enabling it.

## Telemetry events

Debug telemetry should include:

- `bridge_disabled_reject`;
- `queue_accept`;
- `queue_full_reject`;
- `transport_send_attempt`;
- `transport_send_success`;
- `transport_send_failure`;
- `message_timeout`;
- `duplicate_drop`;
- `publish_to_app_attempt`;
- `publish_to_app_success`;
- `publish_to_app_failure`.

Telemetry should include queue depth and reason codes, not raw private content.

## Tests required before bridge-enabled phone runtime

Add fake/unit tests proving:

- disabled bridge rejects without enqueueing;
- queue accepts up to the configured limit;
- queue rejects newest after the limit;
- duplicate IDs do not publish twice;
- timeout removes or marks an item failed;
- retry count is bounded;
- rejected blank/overlong text never reaches a transport callback;
- shutdown drains or discards queues deterministically.
