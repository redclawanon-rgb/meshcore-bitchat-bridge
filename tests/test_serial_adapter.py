import io
import json
import unittest
from contextlib import redirect_stdout

from tools import bridge_serial
from tools.bridge_frame_codec import BridgeFrameError
from tools.bridge_frame_codec.serial_adapter import (
    InMemorySerialByteStream,
    MAX_SERIAL_PAYLOAD,
    SERIAL_RX_START,
    SERIAL_TX_START,
    SerialCompanionDatagramTransport,
    SerialRxPacketReader,
    unwrap_serial_tx_packet,
    wrap_serial_rx_packet,
    wrap_serial_tx_packet,
)
from tools.bridge_frame_codec.sim import SimulatedBridgeNode, SimulatedMeshCoreLink
from tools.bridge_frame_codec.transport import drain_transport_to_node


class FakeByteStream:
    def __init__(self, incoming: bytes = b""):
        self.incoming = bytearray(incoming)
        self.writes: list[bytes] = []

    def write(self, data: bytes) -> int:
        self.writes.append(data)
        return len(data)

    def read(self, size: int = 1) -> bytes:
        if not self.incoming:
            return b""
        chunk = bytes(self.incoming[:size])
        del self.incoming[:size]
        return chunk


class SerialAdapterTests(unittest.TestCase):
    def test_wrap_serial_tx_packet(self):
        packet = wrap_serial_tx_packet(b"\x3e\x01\xff\xff\xffabc")

        self.assertEqual(packet[0], SERIAL_TX_START)
        self.assertEqual(packet[1:3], (8).to_bytes(2, "little"))
        self.assertEqual(packet[3:], b"\x3e\x01\xff\xff\xffabc")

    def test_wrap_serial_rejects_oversize_payload(self):
        with self.assertRaisesRegex(BridgeFrameError, "serial payload too large"):
            wrap_serial_tx_packet(b"x" * (MAX_SERIAL_PAYLOAD + 1))

    def test_unwrap_serial_tx_packet_validates_envelope(self):
        command = b"\x3e\x01\xff\xff\xffabc"

        self.assertEqual(unwrap_serial_tx_packet(wrap_serial_tx_packet(command)), command)
        with self.assertRaisesRegex(BridgeFrameError, "too short"):
            unwrap_serial_tx_packet(b"\x3c\x01")
        with self.assertRaisesRegex(BridgeFrameError, "unexpected serial TX start"):
            unwrap_serial_tx_packet(wrap_serial_rx_packet(command))
        with self.assertRaisesRegex(BridgeFrameError, "length mismatch"):
            unwrap_serial_tx_packet(b"\x3c\x04\x00abc")

    def test_serial_rx_reader_extracts_packet_across_chunks_and_discards_junk(self):
        reader = SerialRxPacketReader()
        notification = b"\x1b\x00\x00\x00\x01\xff\xff\xff\x00"
        serial_packet = b"junk" + wrap_serial_rx_packet(notification)

        self.assertEqual(reader.feed(serial_packet[:5]), [])
        self.assertEqual(reader.feed(serial_packet[5:]), [notification])
        self.assertEqual(reader.feed(b""), [])

    def test_serial_rx_reader_extracts_multiple_packets(self):
        reader = SerialRxPacketReader()
        one = wrap_serial_rx_packet(b"one")
        two = wrap_serial_rx_packet(b"two")

        self.assertEqual(reader.feed(one + two), [b"one", b"two"])

    def test_serial_rx_packet_from_simulated_notification_reaches_node(self):
        alice = SimulatedBridgeNode(bridge_id=1)
        bob = SimulatedBridgeNode(bridge_id=2)
        link = SimulatedMeshCoreLink()
        command = alice.make_text_commands("serial path")[0]
        notification = link.command_to_notification(command)
        reader = SerialRxPacketReader()

        [payload] = reader.feed(wrap_serial_rx_packet(notification))
        delivered = bob.receive_notification(payload)

        self.assertIsNotNone(delivered)
        assert delivered is not None
        self.assertEqual(delivered.text, "serial path")

    def test_serial_dry_run_cli_outputs_tx_packet(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = bridge_serial.main(["--port", "/dev/null", "dry run"])
        payload = json.loads(buf.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"], "dry-run-no-port-opened")
        self.assertEqual(payload["port"], "/dev/null")
        self.assertEqual(payload["packet_count"], 1)
        self.assertTrue(payload["packets"][0]["serial_tx_hex"].startswith("3c"))

    def test_serial_dry_run_packet_replays_through_fake_stream_to_receiver(self):
        text = "dry-run orchestration smoke"
        bob = SimulatedBridgeNode(bridge_id=0xB2)
        link = SimulatedMeshCoreLink()
        stream = InMemorySerialByteStream()
        transport = SerialCompanionDatagramTransport(byte_stream=stream)
        dry_run = bridge_serial.run(
            bridge_serial.build_parser().parse_args(
                ["--bridge-id", "0xa1", "--port", "/dev/not-opened", text]
            )
        )

        self.assertEqual(dry_run["mode"], "dry-run-no-port-opened")
        self.assertEqual(dry_run["port"], "/dev/not-opened")
        self.assertEqual(stream.writes, [])
        packets = dry_run["packets"]
        self.assertIsInstance(packets, list)
        assert isinstance(packets, list)
        for item in packets:
            assert isinstance(item, dict)
            serial_tx_packet = bytes.fromhex(item["serial_tx_hex"])
            command = unwrap_serial_tx_packet(serial_tx_packet)
            self.assertEqual(command.hex(), item["companion_command_hex"])
            stream.inject_notification(link.command_to_notification(command))
        delivered = drain_transport_to_node(transport, bob)

        self.assertEqual([item.text for item in delivered], [text])
        self.assertEqual([item.text for item in bob.inbox], [text])
        self.assertIsNone(transport.recv_channel_data_notification())

    def test_serial_transport_default_does_not_open_or_write_port(self):
        transport = SerialCompanionDatagramTransport(port="/dev/ttyUSB0")

        transport.send_channel_data_command(b"abc")

        self.assertIsNone(transport.byte_stream)
        self.assertEqual(transport.sent_packets, [wrap_serial_tx_packet(b"abc")])
        self.assertIsNone(transport.recv_channel_data_notification())

    def test_serial_transport_uses_fake_byte_stream_for_send_and_recv(self):
        stream = FakeByteStream(incoming=wrap_serial_rx_packet(b"notify"))
        transport = SerialCompanionDatagramTransport(byte_stream=stream, read_size=4)

        transport.send_channel_data_command(b"cmd")

        self.assertEqual(stream.writes, [wrap_serial_tx_packet(b"cmd")])
        self.assertIsNone(transport.recv_channel_data_notification())
        self.assertIsNone(transport.recv_channel_data_notification())
        self.assertEqual(transport.recv_channel_data_notification(), b"notify")
        self.assertIsNone(transport.recv_channel_data_notification())

    def test_serial_transport_real_open_requires_explicit_gate(self):
        opened: list[tuple[object, ...]] = []

        def fake_factory(*args, **kwargs):
            opened.append((args, kwargs))
            return FakeByteStream()

        SerialCompanionDatagramTransport(
            port="/fake/tty",
            baud=9600,
            serial_factory=fake_factory,
        )
        self.assertEqual(opened, [])

        transport = SerialCompanionDatagramTransport(
            port="/fake/tty",
            baud=9600,
            open_real_port=True,
            serial_factory=fake_factory,
        )
        self.assertIsInstance(transport.byte_stream, FakeByteStream)
        self.assertEqual(opened, [(("/fake/tty", 9600), {"timeout": 0})])


if __name__ == "__main__":
    unittest.main()
