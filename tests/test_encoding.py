from src.decoding import CircuitDecoder
from src.encoding import CircuitEncoder
from src.optimization_level import OptimizationLevel
from src.schematics import SchematicsBuilder


def test_roundtrip():
    builder = SchematicsBuilder(OptimizationLevel.FAST)
    builder.build_circuits()
    schematics = builder.schematics

    reference_encoding = CircuitEncoder(schematics).encode()
    round_trip_schematics = CircuitDecoder(
        reference_encoding, OptimizationLevel.FAST
    ).decode()
    round_trip_encoding = CircuitEncoder(round_trip_schematics).encode()

    if reference_encoding != round_trip_encoding:
        print("Encoding is different after round trip")
        for idx, (a, b) in enumerate(zip(reference_encoding, round_trip_encoding)):
            if a != b:
                print(f"Index {idx} is different: {a} != {b}")
                assert False
