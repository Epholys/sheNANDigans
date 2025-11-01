import itertools
from typing import List, Tuple

from bitarray import bitarray

from nand.circuit_builder import CircuitLibrary
from nand.circuit_encoder import CircuitEncoder

type Length = int
type Percentage = float
type EncodingStats = Tuple[Length, Percentage]


def compare_encoders(
    encoders: list[CircuitEncoder], libraries: list[Tuple[CircuitLibrary, str]]
) -> None:
    """Compare the encoders and print the encoding stats."""
    encoding_stats = _compute_stats(encoders, libraries)

    # Compute column widths
    encoder_name_width = (
        max(len(encoder.__class__.__name__) for encoder in encoders) + 2
    )
    library_name_width = max(len(library[1]) for library in libraries) + 2
    bit_width = max(len(str(s[2][0])) for s in encoding_stats)  # width for bit count
    max_len = max(s[2][0] for s in encoding_stats)
    max_len_width = 100
    ratio = max_len_width / max_len

    for encoder, library, (bit_count, percent) in encoding_stats:
        print(
            f"{encoder.__class__.__name__:<{encoder_name_width}} "
            f"{library[1]:<{library_name_width}} "
            f"{bit_count:>{bit_width}} bits  "
            f"({percent:>6.2f}%) "
            f"{'.' * int(bit_count * ratio)}"
        )


def _compute_stats(
    encoders: list[CircuitEncoder], libraries: list[Tuple[CircuitLibrary, str]]
):
    length_stats: List[Tuple[CircuitEncoder, Tuple[CircuitLibrary, str], Length]] = []
    for encoder, library in itertools.product(encoders, libraries):
        encoding = encoder.encode(library[0])
        length = 0
        if isinstance(encoding, bitarray):
            length = len(encoding)
        elif isinstance(encoding, list):
            length = (
                len(encoding) * 16
            )  # 16 bits per int TODO: for every new big circuit, test if it enough
        print(encoding.to01())

        length_stats.append((encoder, library, length))
    length_stats.sort(key=lambda x: -x[2])

    encoding_stats: List[
        Tuple[CircuitEncoder, Tuple[CircuitLibrary, str], EncodingStats]
    ] = []
    for encoder, library, length in length_stats:
        percentage = length / length_stats[0][2] * 100
        encoding_stats.append((encoder, library, (length, percentage)))

    return encoding_stats
