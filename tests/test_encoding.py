from typing import Type
from nand.bit_packed_encoder import BitPackedEncoder
from nand.circuit_decoder import CircuitDecoder
from nand.circuit_encoder import CircuitEncoder
from nand.default_decoder import DefaultDecoder
from nand.default_encoder import DefaultEncoder
from nand.schematics import SchematicsBuilder
from nand.scratchpad import BitPackedDecoder


def test_default_encoder():
    _test_roundtrip(DefaultEncoder, DefaultDecoder)


def test_bit_packed_encoder():
    _test_roundtrip(BitPackedEncoder, BitPackedDecoder)


def _test_roundtrip(encoder: Type[CircuitEncoder], decoder: Type[CircuitDecoder]):
    """Test the round trip encoding and decoding.

    It tests the raw values of the encoding and decoding, not the actual circuits.
    """
    builder = SchematicsBuilder()
    builder.build_circuits()
    schematics = builder.schematics

    reference_encoding = encoder().encode(schematics)
    round_trip_schematics = decoder(reference_encoding).decode()
    round_trip_encoding = encoder().encode(round_trip_schematics)

    if reference_encoding != round_trip_encoding:
        if len(reference_encoding) != len(round_trip_encoding):
            assert False, (
                f"Encoding is different after round trip: "
                f"Length is different: {len(reference_encoding)} != {len(round_trip_encoding)}"
            )
        for idx, (a, b) in enumerate(zip(reference_encoding, round_trip_encoding)):
            if a != b:
                assert False, (
                    f"Encoding is different after round trip: "
                    f"Index {idx} is different: {a} != {b}"
                )
