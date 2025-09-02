from typing import List


def read_bits(data: List[int], n: int) -> int:
    """Convert the first n bits from a list (integer of value 0 or 1) to an integer."""
    if len(data) < n:
        raise ValueError(
            f"Not enough bits in data (of len {len(data)})"
            f"to form an integer with {n} requested bits."
        )
    bits = [data.pop(0) for _ in range(n)]
    return sum(bit << i for i, bit in enumerate(reversed(bits)))


def read_bits_with_offset(data: List[int], n: int) -> int:
    """Convert the first n bits from a list (integer of value 0 or 1) to an integer,
    with an offset of +1.

    This offset make a '0' become 1, '1' become 2, '10' become 3, etc.
    See 'BitPackedEncoder' for rational.
    """
    return read_bits(data, n) + 1


def bitlength_with_offset(n: int):
    """Calculate the bit length needed to represent an integer, minus an offset.
    Returns 1 for 0, otherwise returns the bit length of n.

    This offset makes for example the value 8, which would be encoded as '1000',
    so with a bitlength of 4, into the value 7, which is encoded as '111',so with a
    bitlength and so return value of 3.

    See 'BitPackedEncoder' for rational.
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
    """Converts an integer to a list of bits of a specific size, with an offset

    This offset makes for example the value 8, which would be returned as [1, 0, 0, 0],
    into the value 7, which is encoded as [1, 1, 1] which is the effective return value.

    See 'BitPackedEncoder' for rational.
    """
    return int2bitlist(n - 1, bit_size)
