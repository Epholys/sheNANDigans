import unittest

from src.decoding import CircuitDecoder
from src.encoding import CircuitEncoder
from src.schematics import SchematicsBuilder


class TestEncoding(unittest.TestCase):
    def test_roundtrip(self):
        builder = SchematicsBuilder()
        builder.build_circuits()
        schematics = builder.schematics

        reference_encoding = CircuitEncoder(schematics).encode()
        round_trip_schematics = CircuitDecoder(reference_encoding).decode()
        round_trip_encoding = CircuitEncoder(round_trip_schematics).encode()

        if reference_encoding != round_trip_encoding:
            print(f"{self.id()}: Encoding is different after round trip")
            for idx, (a, b) in enumerate(zip(reference_encoding, round_trip_encoding)):
                if a != b:
                    print(f"Index {idx} is different: {a} != {b}")
            assert False
