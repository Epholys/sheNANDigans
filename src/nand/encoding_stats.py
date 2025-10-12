from typing import List, Tuple
from nand.circuit_encoder import CircuitEncoder
from nand.circuit_builder import CircuitLibrary

type Length = int
type Percentage = float
type EncodingStats = Tuple[Length, Percentage]


def compare_encoders(encoders: List[CircuitEncoder], library: CircuitLibrary) -> None:
    """Compare the encoders and print the encoding stats."""
    encoding_stats = _compute_stats(encoders, library)

    # Compute column widths
    name_width = max(len(encoder.__class__.__name__) for encoder in encoders) + 2
    bit_width = max(len(str(s[1][0])) for s in encoding_stats)  # width for bit count
    max_len = max(s[1][0] for s in encoding_stats)
    max_len_width = 100
    ratio = max_len_width / max_len

    for encoder, (bit_count, percent) in encoding_stats:
        print(
            f"{encoder.__class__.__name__:<{name_width}} "
            f"{bit_count:>{bit_width}} bits  "
            f"({percent:>6.2f}%) "
            f"{'.' * int(bit_count * ratio)}"
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
