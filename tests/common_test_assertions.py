from itertools import product
import random
from re import S
from typing import Any, Callable, Iterable, List, Sequence, Tuple, Union
from nand.circuit import Circuit
from nand.simulator import SimulationResult, Simulator


def _to_list(x: Any) -> List[Any]:
    """Convert everything into a list:

    - string 'str' or bytes 'bytes' become '[str]' and '[bytes]
    - dictionaries become a list of items: '[(key1, value1), (key2, value2), ...]'
    - other iterables are converted to list.
    - single value become a singleton list.
    """
    match x:
        case str() | bytes():
            return [x]
        case dict():
            return list(x.items())
        case _ if isinstance(x, Iterable):
            return list(x)
        case _:
            return [x]


def _flatten(list: Sequence[Any]) -> List[Any]:
    """Flatten any sequence of objects.

    The objects does not need to be an iterable, they will be converted into a list.
    """
    return [item for sublist in list for item in _to_list(sublist)]


def _assert_circuit_signature(circuit: Circuit, n_inputs: int, n_outputs: int):
    """Assert the signature of a circuit (number of inputs and outputs)."""
    circuit_name: str = circuit.name

    assert len(circuit.inputs) == n_inputs, (
        f"\nCircuit {circuit_name}: Signature mismatch:"
        f"\nActual input length = {len(circuit.inputs)}"
        f"\nExpected input length = {n_inputs}"
    )
    assert len(circuit.outputs) == n_outputs, (
        f"\nCircuit {circuit_name}: Signature mismatch:"
        f"\nActual output length = {len(circuit.outputs)}"
        f"\nExpected output length = {n_outputs}"
    )


def _assert_result(
    result: SimulationResult,
    case: Sequence[bool] | Sequence[list[bool]],
    expected: bool | Sequence[bool],
    circuit_name: str,
):
    """Assert the simulation result.

    Support both basic gates and multi-bits gates.
    """
    if not result:
        assert False, (
            f"\nCircuit {circuit_name}: Simulation failed for inputs: "
            f"{' '.join(str(int(i)) for i in _to_list(case))}"
        )

    # TODO: take into account bit width
    assert result == _to_list(expected), (
        f"\nCircuit {circuit_name} failed:"
        f"\n  Inputs:   {' '.join(str(int(i)) for i in _flatten(case))}"
        f"\n  Expected: {' '.join(str(int(i)) for i in _to_list(expected))}"
        f"\n  Actual:   {' '.join(str(int(i)) for i in result)}"
    )


# Typing for basic gates operation: few inputs and few outputs.
BoolFunc = Union[
    Callable[[bool], bool],
    Callable[[bool, bool], bool],
    Callable[[bool, bool, bool], bool],
    Callable[[bool], Tuple[bool, bool]],
    Callable[[bool, bool], Tuple[bool, bool]],
    Callable[[bool, bool, bool], Tuple[bool, bool]],
]


def assert_basic_gate(
    simulator: Simulator, gate_logic: BoolFunc, n_in: int = 2, n_out: int = 1
):
    """Assert the simulation of a logic gate.

    Tests all possibles values.

    Parameters:
        simulator:  Simulator for the circuit being tested.
        gate_logic: The logic operation the gate should be doing.
        n_in:       The number of inputs.
        n_out:      The number of outputs.
    """
    _assert_circuit_signature(simulator._circuit, n_inputs=n_in, n_outputs=n_out)

    # Generate all possible values.
    input_cases = list(product([True, False], repeat=n_in))

    for case in input_cases:
        expected = gate_logic(*case)
        result = simulator.simulate(case)

        _assert_result(result, case, expected, simulator._circuit.name)


BitwiseBoolFunc = Callable[[List[List[bool]]], List[bool]]


def assert_bitwise_gate(
    simulator: Simulator,
    gate_logic: BitwiseBoolFunc,
    dimension: int,
    n_ins: int,
    seed: int = 0,
    n_random_ins: int = 3,
):
    """Assert the simulation of a more complex bitwise gate.

    Only test a selection of value.

    Parameters:
        simulator:      Simulator for the circuit being tested.
        gate_logic:     The logic operation the gate should be doing.
        dimension:      The dimension of the input.
                        For example: 8 means that the inputs are 8 bits wide.
        n_in:           The number of inputs.
        seed:           The seed for the random number generator,
                        for deterministic behavior
        n_random_ins:   How many random inputs to try
    """
    _assert_circuit_signature(
        simulator._circuit, n_inputs=n_ins * dimension, n_outputs=dimension
    )

    input_lists: List[List[bool]] = []

    # Hard-coded inputs
    # - All True
    # - All False
    # - Interleaved True / False.
    # - Interleaved True / False in a 2-1 pattern.
    input_lists.append([True for _ in range(dimension)])
    input_lists.append([False for _ in range(dimension)])
    input_lists.append([True if i % 2 else False for i in range(dimension)])
    input_lists.append([False if i % 2 else True for i in range(dimension)])
    input_lists.append([False if i % 2 else True for i in range(dimension)])
    input_lists.append([True if i % 3 else False for i in range(dimension)])

    # Random inputs value. Deterministic using a seed.
    random.seed(seed)
    for _ in range(n_random_ins):
        input_lists.append([bool(random.randint(0, 1)) for _ in range(dimension)])

    input_cases = list(product(input_lists, repeat=n_ins))

    for case in input_cases:
        expected = gate_logic(list(case))
        result = simulator.simulate(_flatten(case))

        _assert_result(result, case, expected, simulator._circuit.name)
