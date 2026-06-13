# Threat Model

## MVP security posture

MVP is lab-only unless and until encrypted tunneling is implemented. Do not market or present MVP text bridging as preserving bitchat's full privacy/security model.

## Assets

- User message content
- Sender/recipient metadata
- Bridge identity mapping
- MeshCore node identity

## MVP risks

- Plaintext bridge messages may be readable by bridge endpoints.
- LoRa metadata may reveal activity/location/routing patterns.
- Relay loops can duplicate or amplify traffic.
- Nickname/identity spoofing is possible until signatures/mapping are added.

## Later security goals

- Tunnel encrypted bitchat payloads end-to-end.
- Carry signed bridge adverts.
- Clearly distinguish transport security from application-layer E2EE.
