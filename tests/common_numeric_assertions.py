from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from itertools import product
import multiprocessing
from nand.simulator import Simulator
from tests.numeric_operations import NumericOperations
from tests.common_gate_assertions import (
    assert_circuit_signature,
    assert_simulation_result,
)


@dataclass(frozen=True)
class NumericCircuitCase:
    simulator: Simulator
    operations: NumericOperations
    inputs: tuple[bool, ...]


def _assert_single_numeric_simulation(
    case: NumericCircuitCase, chunk_size: int | None = None
):
    """Assert the simulation of a numeric operation for a single case."""

    expected = case.operations.apply(case.inputs)
    result = case.simulator.simulate(case.inputs)

    assert_simulation_result(
        result, case.inputs, expected, case.simulator._circuit.name, chunk_size
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
    """
    assert_circuit_signature(simulator._circuit, n_inputs, n_outputs)

    all_possible_inputs = list(product([True, False], repeat=n_inputs))

    cases = [
        NumericCircuitCase(simulator, operations, inputs)
        for inputs in all_possible_inputs
    ]

    if n_inputs >= 16:
        n_tasks = len(cases)

        # This is based on almost nothing (well with hyperfine on a ~5s task).
        # There's a big difference between Windows (5.5s) and WSL (3.6s).
        # I know it's because of how the threads/processes are managed between different OSes.
        # I try quickly asking LLMs (2025-03-14 : GPT-4o and Claude 3.7), but they have different opinions.
        # When I profile with 'python -m cProfile', on both OSes it seems that the hyper-parameters of workers and chunks are not optimized:
        # the process management takes the biggest amount of time (Windows's '_winapi.WaitForMultipleObjects' and WSL's 'select.poll').
        # I'll come back later, when I have more tests and more motivation to go deeper on this subject.
        # Things I know (now) that I can try:
        # - Keeping this approach:
        #   - Automated hyper-parameters tuning
        #   - psutil library
        #   - 'multiprocessing.Pool'
        #   - loky's 'joblib.Parallel'
        #   - Persistent worker pool 'multiprocessing.Pool'
        #   - Persistent workers (probably a good idea when I'll have more parallelizable tests)
        #   - Different chunking approach: not in 'executor.map(chunksize=)' but pre-chunking: 'chunks=[cases[i+chunk_size] for i in range(len(cases), chunk_size)]'
        #   - Pre-compute NumericOperations (or at least the inputs)
        #   - Analyze pickling
        # - Other approaches: changing the simulation philosophy:
        #   - Parallel simulation using topological order
        #   - Parallel simulation using circuit partitioning
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
            _assert_single_numeric_simulation(case, chunk_size=bit_width)
