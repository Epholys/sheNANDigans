from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from itertools import product
import multiprocessing
import random
from nand.simulator import Simulator
from tests.sequence_utils import _flatten, _to_list
from tests.numeric_operations import NumericOperations
from tests.common_gate_assertions import (
    assert_circuit_signature,
    assert_simulation_result,
)


@dataclass(frozen=True)
class NumericCircuitCase:
    """Parameters of a test cas for a numeric circuit."""

    simulator: Simulator
    operations: NumericOperations
    inputs: list[bool]


def _assert_single_numeric_simulation(
    case: NumericCircuitCase, bit_width: int | None = None
):
    """Assert the simulation of a numeric operation for a single case.

    Parameters:
    case:       The tested case.
    chunk_size: Used to chunk the inputs, for easy multi-line displaying
                of multi-bits inputs.
    """

    # Apply the operations to go from inputs to expected outputs.
    expected = case.operations.apply(case.inputs)

    # Simulate the tested circuit to get the tested result.
    result = case.simulator.simulate(case.inputs)

    assert_simulation_result(
        result,
        case.inputs,
        expected,
        case.simulator._circuit.name,
        chunk_size=bit_width,
    )


def assert_all_numeric_simulations(
    simulator: Simulator,
    n_inputs: int,
    n_outputs: int,
    operations: NumericOperations,
    bit_width: int | None = None,
):
    """Assert the behavior of a circuit implementing a numeric operation for all
    possible inputs.

    Parameters:
    simulator:  The simulator of the tested circuit
    n_inputs:   The number of inputs
    n_outputs:  The number of outputs
    operation:  The operations to apply to the inputs to get the expected outputs.
    bit_width:  The bit width of the operands. Used to chunk the inputs, for easy
                multi-line pretty printing.
    """
    assert_circuit_signature(simulator._circuit, n_inputs, n_outputs)

    all_possible_inputs = list(product([True, False], repeat=n_inputs))

    cases = [
        NumericCircuitCase(simulator, operations, _to_list(inputs))
        for inputs in all_possible_inputs
    ]

    if n_inputs >= 16:
        n_tasks = len(cases)

        # This is based on almost nothing (well with hyperfine on a ~5s task).
        # There's a big difference between Windows (5.5s) and WSL (3.6s).
        #
        # I know it's because of how the threads/processes are managed
        # between different OSes.
        # I try quickly asking LLMs (2025-03-14 : GPT-4o and Claude 3.7),
        #
        # but they have different opinions.
        # When I profile with 'python -m cProfile', on both OSes it seems that
        # the hyper-parameters of workers and chunks are not optimized:
        # the process management takes the biggest amount of time
        # (Windows's '_winapi.WaitForMultipleObjects' and WSL's 'select.poll').
        #
        # I'll come back later, when I have more tests and more motivation to go deeper
        # on this subject.
        # Things I know (now) that I can try:
        # - Keeping this approach:
        #   - Automated hyper-parameters tuning
        #   - psutil library
        #   - 'multiprocessing.Pool'
        #   - loky's 'joblib.Parallel'
        #   - Persistent worker pool 'multiprocessing.Pool'
        #   - Persistent workers (probably a good idea when I'll have more
        #     parallelizable tests)
        #   - Different chunking approach: not in 'executor.map(chunksize=)' but
        #     pre-chunking:
        #     'chunks=[cases[i+chunk_size] for i in range(len(cases), chunk_size)]'
        #   - Pre-compute NumericOperations (or at least the inputs)
        #   - Analyze pickling
        # - Other approaches: changing the simulation philosophy:
        #   - Parallel simulation using topological order
        #   - Parallel simulation using circuit partitioning
        #   - Re-computing only the changed wires
        #   - Using lower-level libraries (Cython, Numba, NumPy, CuPy, etc.)
        cpu_count = multiprocessing.cpu_count()
        n_processes = cpu_count - 1
        chunk_size = max(1, n_tasks // (n_processes * 4))

        with ProcessPoolExecutor(max_workers=n_processes) as executor:
            results = list(
                executor.map(
                    _assert_single_numeric_simulation,
                    cases,
                    chunksize=chunk_size,
                )
            )
        assert len(results) == n_tasks

    else:
        for case in cases:
            _assert_single_numeric_simulation(case, bit_width=bit_width)


def assert_partial_numeric_simulation(
    simulator: Simulator,
    n_inputs: int,
    n_outputs: int,
    n_bits: int,
    operations: NumericOperations,
    seed: int = 0,
    n_random_ins: int = 3,
):
    assert_circuit_signature(simulator._circuit, n_inputs * n_bits, n_outputs * n_bits)

    # Test some common edge cases.
    inputs_lists: list[list[bool]] = []
    inputs_lists.append([True for _ in range(n_bits)])
    inputs_lists.append([False for _ in range(n_bits)])
    inputs_lists.append([True if i == 0 else False for i in range(n_bits)])
    inputs_lists.append([False if i == 0 else True for i in range(n_bits)])
    inputs_lists.append([True if i == n_bits - 1 else False for i in range(n_bits)])
    inputs_lists.append([False if i == n_bits - 1 else True for i in range(n_bits)])

    # Random inputs value. Deterministic using a seed.
    random.seed(seed)
    for _ in range(n_random_ins):
        inputs_lists.append([bool(random.randint(0, 1)) for _ in range(n_bits)])

    cases = list(product(inputs_lists, repeat=n_inputs))

    for case in cases:
        _assert_single_numeric_simulation(
            NumericCircuitCase(simulator, operations, _flatten(case)), bit_width=n_bits
        )
