from functools import partial
from typing import Callable, List, Tuple


class NumericOperations:
    def __init__(
        self,
        inputs_to_numbers: Callable[[List[bool]], List[int]],
        number_to_outputs: Callable[[int], List[bool]],
        operation: Callable[[List[int]], int],
    ):
        self.inputs_to_numbers = inputs_to_numbers
        self.number_to_outputs = number_to_outputs
        self.operation = operation

    def apply(self, inputs: Tuple[bool, ...]) -> List[bool]:
        input_numbers = self.inputs_to_numbers(list(inputs))
        operation_result = self.operation(input_numbers)
        expected_outputs = self.number_to_outputs(operation_result)
        return expected_outputs


def bools_to_int(bools: List[bool]):
    """
    bools from low to high
    """
    return sum(b * (2**n) for n, b in enumerate(bools))


def _int_to_bools(x: int, n: int) -> List[bool]:
    """
    bools from low to high
    """
    return [(x >> shift) & 1 > 0 for shift in range(n)]


def int_to_bools(n: int) -> Callable[[int], List[bool]]:
    return partial(_int_to_bools, n=n)
