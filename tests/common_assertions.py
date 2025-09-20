from itertools import batched
from typing import Sequence
from nand.circuit import Circuit
from nand.simulator import SimulationResult
from tests.sequence_utils import _flatten, _to_list


def assert_circuit_signature(circuit: Circuit, n_inputs: int, n_outputs: int):  # noqa: F821
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


def assert_simulation_result(
    result: SimulationResult,
    inputs: Sequence[bool] | Sequence[list[bool]],
    expected: bool | Sequence[bool],
    circuit_name: str,
    chunk_size: int | None = None,
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
        assert False, f"\nCircuit {circuit_name}: Simulation failed"

    inputs_prefix = "  Inputs:   "
    inputs_01 = [str(int(i)) for i in _flatten(inputs)]

    if chunk_size:
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
