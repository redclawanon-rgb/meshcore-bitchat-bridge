import unittest

from tools.bridge_frame_codec import (
    BITCHAT_MESSAGE_TYPE_MESSAGE,
    BITCHAT_PACKET_VERSION_V1,
    BITCHAT_RECIPIENT_BROADCAST,
    BitchatIdentityFixtureError,
    BitchatPacketFixture,
    VerifiedSenderFixtureRegistry,
    canonical_announce_bytes,
    decode_identity_announcement_tlv,
    ed25519_private_key_from_seed,
    ed25519_private_seed_bytes,
    ed25519_public_key_bytes_from_seed,
    ed25519_sign_fixture,
    ed25519_verify_fixture,
    encode_identity_announcement_tlv,
    sign_packet_fixture,
)


class BitchatIdentityFixtureTests(unittest.TestCase):
    def test_deterministic_ed25519_key_bytes_match_fixture_seed(self):
        seed = bytes(range(32))
        private_key = ed25519_private_key_from_seed(seed)

        self.assertEqual(ed25519_private_seed_bytes(private_key), seed)
        self.assertEqual(
            ed25519_public_key_bytes_from_seed(seed).hex(),
            "03a107bff3ce10be1d70dd18e74bc09967e4d6309ba50d5f1ddc8664125531b8",
        )
        with self.assertRaisesRegex(BitchatIdentityFixtureError, "Ed25519 seed must be exactly 32 bytes"):
            ed25519_private_key_from_seed(b"too short")

    def test_canonical_announce_bytes_and_signature_are_deterministic(self):
        seed = bytes(range(32))
        signing_public_key = ed25519_public_key_bytes_from_seed(seed)
        canonical = canonical_announce_bytes(
            peer_id=bytes.fromhex("0102030405060708"),
            noise_public_key=bytes(range(32, 64)),
            signing_public_key=signing_public_key,
            nickname="alice",
            timestamp_ms=0x0000018F3D2A1B00,
        )

        self.assertEqual(
            canonical.hex(),
            "13626974636861742d616e6e6f756e63652d76310102030405060708"
            "202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f"
            "03a107bff3ce10be1d70dd18e74bc09967e4d6309ba50d5f1ddc8664125531b8"
            "05616c6963650000018f3d2a1b00",
        )
        signature = ed25519_sign_fixture(canonical, seed)
        self.assertEqual(
            signature.hex(),
            "aa9cd5cb4562cd1ebec85042ae337d67d1f1f2ec4b367721c1d6cfc7363661f1"
            "4c3798351cfdd9b5de73c401f120f0dc1957aa8e68e75374f023bda93405d200",
        )
        self.assertTrue(ed25519_verify_fixture(signature, canonical, signing_public_key))
        self.assertFalse(ed25519_verify_fixture(signature, canonical + b"!", signing_public_key))

    def test_identity_announcement_tlv_matches_ios_and_android_shape(self):
        tlv = encode_identity_announcement_tlv(
            nickname="alice",
            noise_public_key=bytes(range(32, 64)),
            signing_public_key=ed25519_public_key_bytes_from_seed(bytes(range(32))),
            direct_neighbors=[b"ABCDEFGH"],
        )

        self.assertEqual(
            tlv.hex(),
            "0105616c696365"
            "0220202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f"
            "032003a107bff3ce10be1d70dd18e74bc09967e4d6309ba50d5f1ddc8664125531b8"
            "04084142434445464748",
        )
        decoded = decode_identity_announcement_tlv(tlv)
        self.assertEqual(decoded.nickname, "alice")
        self.assertEqual(decoded.noise_public_key, bytes(range(32, 64)))
        self.assertEqual(decoded.signing_public_key, ed25519_public_key_bytes_from_seed(bytes(range(32))))
        self.assertEqual(decoded.direct_neighbors, (b"ABCDEFGH",))
        with self.assertRaisesRegex(BitchatIdentityFixtureError, "nickname TLV value must be <=255 bytes"):
            encode_identity_announcement_tlv(
                nickname="x" * 256,
                noise_public_key=bytes(range(32, 64)),
                signing_public_key=ed25519_public_key_bytes_from_seed(bytes(range(32))),
            )

    def test_packet_signing_preimage_can_be_signed_and_verified_with_ed25519_fixture(self):
        seed = bytes(range(32))
        signing_public_key = ed25519_public_key_bytes_from_seed(seed)
        packet = BitchatPacketFixture(
            version=BITCHAT_PACKET_VERSION_V1,
            packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            ttl=7,
            timestamp_ms=0x0000018F3D2A1B00,
            sender_id=bytes.fromhex("0102030405060708"),
            recipient_id=BITCHAT_RECIPIENT_BROADCAST,
            payload=b"gate4a fixture",
            signature=bytes([9]) * 64,
        )
        preimage = packet.encode_signing_preimage_v1()
        signature = ed25519_sign_fixture(preimage, seed)

        self.assertEqual(
            signature.hex(),
            "db51d9199a4b3811bbea28dad89318db2a9d6fc5fab18a5a1d91f97d5657146c"
            "b23d451da287cbb673fd48d6b23e3df29310105b0b9dd2c6a5a70e8e3337020d",
        )
        self.assertTrue(ed25519_verify_fixture(signature, preimage, signing_public_key))
        self.assertFalse(ed25519_verify_fixture(signature, packet.encode_raw_v1(), signing_public_key))

    def test_verified_sender_registry_accepts_only_announced_signed_public_text(self):
        seed = bytes(range(32))
        peer_id = bytes.fromhex("0102030405060708")
        announcement_payload = encode_identity_announcement_tlv(
            nickname="alice",
            noise_public_key=bytes(range(32, 64)),
            signing_public_key=ed25519_public_key_bytes_from_seed(seed),
        )
        unsigned_announce = BitchatPacketFixture(
            version=BITCHAT_PACKET_VERSION_V1,
            packet_type=1,
            ttl=7,
            timestamp_ms=0x0000018F3D2A1B00,
            sender_id=peer_id,
            payload=announcement_payload,
        )
        signed_announce = sign_packet_fixture(unsigned_announce, seed)
        signed_public_message = sign_packet_fixture(
            BitchatPacketFixture(
                version=BITCHAT_PACKET_VERSION_V1,
                packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
                ttl=7,
                timestamp_ms=0x0000018F3D2A1B01,
                sender_id=peer_id,
                recipient_id=BITCHAT_RECIPIENT_BROADCAST,
                payload=b"hello verified mesh",
            ),
            seed,
        )

        registry = VerifiedSenderFixtureRegistry()
        with self.assertRaisesRegex(BitchatIdentityFixtureError, "sender has no verified announce"):
            registry.verified_public_text(signed_public_message)

        registered = registry.verify_and_register_announce(signed_announce)
        self.assertEqual(registered.nickname, "alice")

        accepted = registry.verified_public_text(signed_public_message)
        self.assertEqual(accepted.peer_id, peer_id)
        self.assertEqual(accepted.nickname, "alice")
        self.assertEqual(accepted.text, "hello verified mesh")

    def test_verified_sender_registry_rejects_unsigned_and_wrong_key_messages(self):
        seed = bytes(range(32))
        wrong_seed = bytes(range(1, 33))
        peer_id = bytes.fromhex("0102030405060708")
        registry = VerifiedSenderFixtureRegistry()
        registry.verify_and_register_announce(
            sign_packet_fixture(
                BitchatPacketFixture(
                    version=BITCHAT_PACKET_VERSION_V1,
                    packet_type=1,
                    ttl=7,
                    timestamp_ms=0x0000018F3D2A1B00,
                    sender_id=peer_id,
                    payload=encode_identity_announcement_tlv(
                        nickname="alice",
                        noise_public_key=bytes(range(32, 64)),
                        signing_public_key=ed25519_public_key_bytes_from_seed(seed),
                    ),
                ),
                seed,
            )
        )

        unsigned_message = BitchatPacketFixture(
            version=BITCHAT_PACKET_VERSION_V1,
            packet_type=BITCHAT_MESSAGE_TYPE_MESSAGE,
            ttl=7,
            timestamp_ms=0x0000018F3D2A1B01,
            sender_id=peer_id,
            recipient_id=BITCHAT_RECIPIENT_BROADCAST,
            payload=b"unsigned",
        )
        with self.assertRaisesRegex(BitchatIdentityFixtureError, "signed public message is required"):
            registry.verified_public_text(unsigned_message)

        wrong_key_signed_message = sign_packet_fixture(unsigned_message, wrong_seed)
        with self.assertRaisesRegex(BitchatIdentityFixtureError, "signature did not verify"):
            registry.verified_public_text(wrong_key_signed_message)

        bad_announce = sign_packet_fixture(
            BitchatPacketFixture(
                version=BITCHAT_PACKET_VERSION_V1,
                packet_type=1,
                ttl=7,
                timestamp_ms=0x0000018F3D2A1B02,
                sender_id=bytes.fromhex("1112131415161718"),
                payload=encode_identity_announcement_tlv(
                    nickname="mallory",
                    noise_public_key=bytes(range(64, 96)),
                    signing_public_key=ed25519_public_key_bytes_from_seed(seed),
                ),
            ),
            wrong_seed,
        )
        with self.assertRaisesRegex(BitchatIdentityFixtureError, "announce signature did not verify"):
            registry.verify_and_register_announce(bad_announce)


if __name__ == "__main__":
    unittest.main()
