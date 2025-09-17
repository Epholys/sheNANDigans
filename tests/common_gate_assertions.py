from functools import reduce
from itertools import batched, product
import random
from typing import Any, Callable, Iterable, List, Sequence, Tuple, Union
from nand.bit_packed_encoder import int2bitlist
from nand.bits_utils import bitlength_with_offset
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


def assert_circuit_signature(circuit: Circuit, n_inputs: int, n_outputs: int):
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
    inputs: Sequence[bool] | Sequence[list[bool]],
    expected: bool | Sequence[bool],
    circuit_name: str,
    chunk_size: int = 0,
):
    """Assert the simulation result and pretty-display if failure

    Support both basic gates and multi-bits/multi-way gates.

    Parameters:
        result:         The result of the simulation (False or the output)
        inputs:         The inputs of the circuit, for pretty-displaying.
        expected:       The expected result.
        circuit_name:   The name of the circuit, for pretty-displaying.
        chunk_size:     Used to chunk the inputs, for easy multi-line displaying
                        of multi-bits inputs.
    """
    if not result:
        assert False, (
            f"\nCircuit {circuit_name}: Simulation failed for inputs: "
            f"{' '.join(str(int(i)) for i in _to_list(inputs))}"
        )

    inputs_prefix = "  Inputs:   "
    inputs_01 = [str(int(i)) for i in _flatten(inputs)]

    if chunk_size > 0:
        chunks = [" ".join(chunk) for chunk in batched(inputs_01, chunk_size)]
    else:
        chunks = [" ".join(inputs_01)]

    padding = "\n" + " " * len(inputs_prefix)
    inputs_str = f"{inputs_prefix}{padding.join(chunks)}"

    assert result == _to_list(expected), (
        f"\nCircuit {circuit_name} failed:"
        f"\n{inputs_str}"
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
    simulator: Simulator, operation: BoolFunc, n_in: int = 2, n_out: int = 1
):
    """Assert the simulation of a logic gate.

    Tests all possibles values.

    Parameters:
        simulator:  Simulator for the circuit being tested.
        operation : The logic operation the gate should be doing.
                    Should have a few inputs and outputs (see type)
        n_in:       The number of inputs.
        n_out:      The number of outputs.

    Inputs:  A, B, ...         (n_in bool input)
    Outputs: OUT_A, OUT_B, ... (n_out bool output)
    Function: operation(A, B, ...) = OUT_A, OUT_B, ...
    """
    assert_circuit_signature(simulator._circuit, n_inputs=n_in, n_outputs=n_out)

    # Generate all possible values.
    input_cases = list(product([True, False], repeat=n_in))

    for case in input_cases:
        expected = operation(*case)
        result = simulator.simulate(case)

        _assert_result(result, case, expected, simulator._circuit.name)


BitwiseBoolFunc = Callable[[List[List[bool]]], List[bool]]


def assert_multibits_gate(
    simulator: Simulator,
    operation: BitwiseBoolFunc,
    m_bits: int,
    n_ins: int,
    seed: int = 0,
    n_random_ins: int = 3,
):
    """Assert the simulation of a gate with multi-bits inputs, with one output.

    Only test a selection of value.

    Parameters:
        simulator:      Simulator for the circuit being tested.
        operation:      The logic operation the gate should be doing.
                        From a list of multi-bits inputs, to a a single multi-bit output
                        (see type)
        m_bits:         The dimension of the input.
                        For example: 8 means that the inputs are 8 bits wide.
        n_in:           The number of inputs.
        seed:           The seed for the random number generator,
                        for deterministic behavior
        n_random_ins:   How many random inputs to try

    Inputs:  A[m_bits], B[m_bits], ...  (n_ins inputs of m_bits width)
    Outputs: OUT[m_bits]                (one out put of m_bits width)
    Function: operation(A, B, ...) = OUT
    """
    assert_circuit_signature(
        simulator._circuit, n_inputs=n_ins * m_bits, n_outputs=m_bits
    )

    input_lists: List[List[bool]] = []

    # Hard-coded inputs
    # - All True
    # - All False
    # - Interleaved True / False.
    # - Interleaved True / False in a 2-1 pattern.
    input_lists.append([True for _ in range(m_bits)])
    input_lists.append([False for _ in range(m_bits)])
    input_lists.append([True if i % 2 else False for i in range(m_bits)])
    input_lists.append([False if i % 2 else True for i in range(m_bits)])
    input_lists.append([False if i % 2 else True for i in range(m_bits)])
    input_lists.append([True if i % 3 else False for i in range(m_bits)])

    # Random inputs value. Deterministic using a seed.
    random.seed(seed)
    for _ in range(n_random_ins):
        input_lists.append([bool(random.randint(0, 1)) for _ in range(m_bits)])

    input_cases = list(product(input_lists, repeat=n_ins))

    for case in input_cases:
        expected = operation(list(case))
        result = simulator.simulate(_flatten(case))

        _assert_result(
            result, case, expected, simulator._circuit.name, chunk_size=m_bits
        )


def assert_n_way_gate(
    simulator: Simulator,
    operation: Callable[[bool, bool], bool],
    n_way: int,
    seed: int = 0,
    n_random_ins: int = 3,
):
    """Assert the simulation of a n_way gate.

    Only test a selection of value.

    Parameters:
        simulator:      Simulator for the circuit being tested.
        operation:      The logic operation the gate should be doing.
                        Should be from a pair of bool to a single bool.
                        It will be applied with 'reduce' to each bit.
        n_way:          The number of bits in the input
        seed:           The seed for the random number generator,
                        for deterministic behavior
        n_random_ins:   How many random inputs to try

    Inputs:  A, B, C, ...  (n_way boolean inputs)
    Outputs: OUT           (one bool output)
    Function: reduce(operation) (= operation(...(operation(operation(A, B), C)...) )
                                (for example : A | B | C | ... or A & B & C & ... )
    """
    assert_circuit_signature(simulator._circuit, n_inputs=n_way, n_outputs=1)

    input_cases: List[List[bool]] = []

    # Hard-coded inputs, more appropriate for these gates.
    input_cases.append([True for _ in range(n_way)])
    input_cases.append([False for _ in range(n_way)])
    input_cases.append([True if i == 0 else False for i in range(n_way)])
    input_cases.append([False if i == 0 else True for i in range(n_way)])
    input_cases.append([True if i == n_way - 1 else False for i in range(n_way)])
    input_cases.append([False if i == n_way - 1 else True for i in range(n_way)])

    # Random inputs value. Deterministic using a seed.
    random.seed(seed)
    for _ in range(n_random_ins):
        input_cases.append([bool(random.randint(0, 1)) for _ in range(16)])

    for case in input_cases:
        expected: bool = reduce(operation, case)
        result = simulator.simulate(case)

        _assert_result(result, case, expected, simulator._circuit.name)


def assert_mux_n_way_m_bits(
    simulator: Simulator,
    n_way: int,
    m_bits: int,
    seed: int = 0,
):
    """Assert the simulation of the n_way dmux.

    Tests all possible values.

    Parameters:
        simulator:  Simulator for the circuit being tested.
        n_way:      The number of inputs numbers.

    N-way M-bits wide MUX:
    Input:    A, B, C, ..., SEL[N] (n_way inputs of m_bits width
                                    + selection of log2(n_way) bits)
    Output:   OUT                  (m_bits width output)
    Function: A if SEL == 0
              B if SEL == 1
              C if SEL == 2
              ...
    """
    selection_size = bitlength_with_offset(n_way)

    assert_circuit_signature(
        simulator._circuit,
        n_inputs=m_bits * n_way + selection_size,
        n_outputs=m_bits,
    )

    # For the n_way inputs of n_bits bits.
    inputs: List[List[bool]] = []

    # Random inputs value. Deterministic using a seed.
    # Hand-picked makes less sense: we just want one of the inputs.
    random.seed(seed)
    for _ in range(n_way):
        inputs.append([bool(random.randint(0, 1)) for _ in range(m_bits)])

    # For all possible selections, test if the correct input is chosen.
    for i in range(n_way):
        selection = [bool(n) for n in int2bitlist(i, selection_size)]
        full_case: list[bool] = _flatten(inputs) + selection
        # SELect the i-th input
        expected = inputs[i]
        result = simulator.simulate(full_case)

        _assert_result(
            result, full_case, expected, simulator._circuit.name, chunk_size=m_bits
        )


def assert_dmux_n_way(simulator: Simulator, n_way: int):
    """Assert the simulation of the n_way dmux.

    Tests all possible values.

    Parameters:
        simulator:  Simulator for the circuit being tested.
        n_way:      The number of outputs requested

    N-way DMUX:
    Input:    IN, SEL[N]
    Output:   A, B, ... (n_way outputs)
    Function: [IN, 0,  0,  ..., 0  ] if SEL == 0
              [0,  IN, 0,  ..., 0  ] if SEL == 1
              [0,  0,  IN, ..., 0  ] if SEL == 2
              [... ... ... ..., ...] if SEL == ...
              [0,  0,  0,  ..., IN ] if SEL == N-1
    """
    selection_len = bitlength_with_offset(n_way)

    # '1 +' for the IN input.
    assert_circuit_signature(
        simulator._circuit,
        n_inputs=1 + selection_len,
        n_outputs=n_way,
    )

    # For both 'IN' possibility:
    for in_ in [True, False]:
        # For all selection possibles, try if its output are correct.
        for sel_int in range(n_way):
            sel_boollist = [bool(i) for i in int2bitlist(sel_int, selection_len)]

            # The full input list: [IN, SEL_N-1, ..., SEL_0]
            input_list = [in_] + sel_boollist

            # Set the 'sel'-th output to 'in_', all others to 'False'
            expected = [in_ if i == sel_int else False for i in range(n_way)]

            result = simulator.simulate(input_list)

            _assert_result(result, input_list, expected, simulator._circuit.name)
