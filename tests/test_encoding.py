from nand.decoding import CircuitDecoder
from nand.encoding import CircuitEncoder
from nand.schematics import SchematicsBuilder


def test_roundtrip():
    """Test the round trip encoding and decoding.

    It tests the raw values of the encoding and decoding, not the actual circuits.
    """
    builder = SchematicsBuilder()
    builder.build_circuits()
    schematics = builder.schematics

    reference_encoding = CircuitEncoder(schematics).encode()
    round_trip_schematics = CircuitDecoder(reference_encoding).decode()
    round_trip_encoding = CircuitEncoder(round_trip_schematics).encode()

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
