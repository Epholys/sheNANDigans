from functools import partial
from typing import Callable, List, Tuple


class NumericOperations:
    """Class to perform numeric operations on boolean inputs and outputs.

    It's used to clarify the operations performed on the inputs and outputs of a tested
    circuit.
    """

    def __init__(
        self,
        inputs_to_numbers: Callable[[List[bool]], List[int]],
        number_to_outputs: Callable[[int], List[bool]],
        operation: Callable[[List[int]], int],
    ):
        self.inputs_to_numbers = inputs_to_numbers
        self.number_to_outputs = number_to_outputs
        self.operation = operation

    def apply(self, tested_inputs: Tuple[bool, ...]) -> List[bool]:
        """Apply the operation to the tested inputs and return the expected outputs for
        a circuit implementing a numeric operation.

        Here are the steps:
        1. Convert the boolean inputs of a logic circuit to numbers using the
        `inputs_to_numbers` function.
        2. Apply the operation to the numbers using the `operation()` function.
        3. Convert the result of the operation to the expected boolean outputs using the
        `number_to_outputs()`.

        For example, if the operation is addition on two numbers, 'inputs_to_numbers()'
        would convert the boolean inputs to integers using power of twos,
        'operation_result()' is simply 'sum', and 'number_to_outputs()' converts this
        resulting integer to a list of booleans using the same power of twos.

        The rational of using these three functions is that a simple bool->int
        conversion can be more complex in the case of interleaved inputs, and vice
        versa for the outputs.
        """
        input_numbers = self.inputs_to_numbers(list(tested_inputs))
        operation_result = self.operation(input_numbers)
        expected_outputs = self.number_to_outputs(operation_result)
        return expected_outputs


def bools_to_int(bools: List[bool]):
    """Convert a list of booleans to an integer, expecting the list to be in low to
    high order.
    """
    return sum(b * (2**n) for n, b in enumerate(bools))


def _int_to_bools(x: int, n: int) -> List[bool]:
    """Convert an integer to a list of booleans, the list will be from low to high order

    This a parameterized function, to avoid the need to compute the length of the list.
    """
    return [(x >> shift) & 1 > 0 for shift in range(n)]


def int_to_bools(n: int) -> Callable[[int], List[bool]]:
    """Convert an integer to a list of booleans, the list will be from low to high order."""
    return partial(_int_to_bools, n=n)
