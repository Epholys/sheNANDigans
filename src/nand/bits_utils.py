from typing import List


def bits2int(data: List[int], n: int) -> int:
    """Convert the first n bits from a list of bits (integer of value 0 or 1) to an
    integer."""
    if len(data) < n:
        raise ValueError("Not enough bits in data to form an integer.")
    bits = [data.pop(0) for _ in range(n)]
    return sum(bit << i for i, bit in enumerate(reversed(bits)))


def bits2int_with_offset(data: List[int], n: int) -> int:
    return bits2int(data, n) + 1


def bitlength_with_offset(n: int):
    """
    # TODO offset to avoid forgiving them ? Like bits2int
    Calculate the bit length needed to represent an integer.
    Returns 1 for 0, otherwise returns the bit length of n.
    """
    return max(1, (n - 1).bit_length())


def int2bitlist(n: int, bit_size: int):
    """Converts an integer to a list of bits of a specific size."""
    if n < 0:
        raise ValueError("Input must be a non-negative integer")

    # Check if n fits in bit_size
    if n >= (1 << bit_size):
        raise ValueError(f"Integer {n} requires more than {bit_size} bits to represent")

    return [(n >> i) & 1 for i in range(bit_size - 1, -1, -1)]


def int2bitlist_with_offset(n: int, bit_size: int):
    return int2bitlist(n - 1, bit_size)
