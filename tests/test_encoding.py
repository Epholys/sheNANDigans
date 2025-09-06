import itertools

import pytest
from tests.parameters_enums import EncoderAlgorithm, Project, parameter_ids


def _build_roundtrip_cases():
    """Build cases: simply the algorithms and the project.

    Look at these enums for all the cases.
    """
    return itertools.product(EncoderAlgorithm, Project)


@pytest.mark.parametrize(
    "algorithm, project", _build_roundtrip_cases(), ids=parameter_ids
)
def test_roundtrip(
    algorithm: EncoderAlgorithm,
    project: Project,
):
    """Test the round trip encoding and decoding.

    It tests the raw values of the encoding and decoding, not the actual circuits.
    """
    encoder, decoder = algorithm.get_encoder(), algorithm.get_decoder()
    library = project.get_builder().build_circuits()

    reference_encoding = encoder().encode(library)
    round_trip_library = decoder().decode(reference_encoding)
    round_trip_encoding = encoder().encode(round_trip_library)

    if reference_encoding != round_trip_encoding:
        if len(reference_encoding) != len(round_trip_encoding):
            assert False, (
                f"Encoding is different after round trip: Length is different: "
                f"{len(reference_encoding)} != {len(round_trip_encoding)}"
            )
        for idx, (a, b) in enumerate(zip(reference_encoding, round_trip_encoding)):
            if a != b:
                assert False, (
                    f"Encoding is different after round trip: "
                    f"Index {idx} is different: {a} != {b}"
                )
