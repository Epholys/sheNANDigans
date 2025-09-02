from typing import List, Tuple
from nand.circuit_encoder import CircuitEncoder
from nand.circuit_builder import CircuitLibrary

type Length = int
type Percentage = float
type EncodingStats = Tuple[Length, Percentage]


def compare_encoders(encoders: List[CircuitEncoder], library: CircuitLibrary) -> None:
    """Compare the encoders and print the encoding stats."""
    encoding_stats = _compute_stats(encoders, library)

    max_width = max(len(encoder.__class__.__name__) for encoder in encoders)

    # Add some padding (e.g., 2 spaces) to make it look nicer
    name_width = max_width + 2

    for encoder, length in encoding_stats:
        print(
            f"{encoder.__class__.__name__:<{name_width}} {length[0]:>4} bits  ({length[1]:>6.2f}%) {'.' * int(length[0] // 32)}"
        )


def _compute_stats(encoders: List[CircuitEncoder], library: CircuitLibrary):
    length_stats: List[Tuple[CircuitEncoder, Length]] = []
    for encoder in encoders:
        encoding = encoder.encode(library)
        length = len(encoding)
        length_stats.append((encoder, length))
    length_stats.sort(key=lambda x: -x[1])

    encoding_stats: List[Tuple[CircuitEncoder, EncodingStats]] = []
    for encoder, length in length_stats:
        percentage = length / length_stats[0][1] * 100
        encoding_stats.append((encoder, (length, percentage)))

    return encoding_stats
