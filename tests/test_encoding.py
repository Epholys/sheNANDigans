from dataclasses import dataclass
import itertools
from typing import Type

import pytest
from nand.bit_packed_decoder import BitPackedDecoder
from nand.bit_packed_encoder import BitPackedEncoder
from nand.circuit_builder import CircuitBuilder
from nand.circuit_decoder import CircuitDecoder
from nand.circuit_encoder import CircuitEncoder
from nand.default_decoder import DefaultDecoder
from nand.default_encoder import DefaultEncoder
from nand.nand2tetris_hack_alu import HackALUBuilder
from nand.playground_circuit_builder import PlaygroundCircuitBuilder


@dataclass
class _Algorithm:
    encoder: Type[CircuitEncoder]
    decoder: Type[CircuitDecoder]


def _build_roundtrip_cases():
    algorithms = [
        _Algorithm(DefaultEncoder, DefaultDecoder),
        _Algorithm(BitPackedEncoder, BitPackedDecoder),
    ]
    builders = [
        PlaygroundCircuitBuilder(),
        HackALUBuilder(),
    ]
    return itertools.product(algorithms, builders)


def _ids(parameter: _Algorithm | CircuitBuilder):
    match parameter:
        case _Algorithm():
            return parameter.encoder.__name__
        case CircuitBuilder():
            return parameter.__class__.__name__


@pytest.mark.parametrize("algorithm, builder", _build_roundtrip_cases(), ids=_ids)
def test_roundtrip(
    algorithm: _Algorithm,
    builder: CircuitBuilder,
):
    """Test the round trip encoding and decoding.

    It tests the raw values of the encoding and decoding, not the actual circuits.
    """
    encoder, decoder = algorithm.encoder, algorithm.decoder
    library = builder.build_circuits()

    reference_encoding = encoder().encode(library)
    round_trip_library = decoder().decode(reference_encoding)
    round_trip_encoding = encoder().encode(round_trip_library)

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
