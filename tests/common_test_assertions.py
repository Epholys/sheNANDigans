from itertools import product
from typing import Callable
from nand.circuit import Circuit
from nand.simulator import Simulator


def assert_circuit_signature(circuit: Circuit, n_inputs: int, n_outputs: int):
    """Assert the signature of a circuit (number of inputs and outputs)."""
    assert len(circuit.inputs) == n_inputs
    assert len(circuit.outputs) == n_outputs


def assert_logic_gate_simulations(
    simulator: Simulator, gate_logic: Callable[[bool, bool], bool]
):
    """Assert the simulation of a logic gate.
    'gate_logic' is the expected behavior of the gate.
    """
    assert_circuit_signature(simulator._circuit, n_inputs=2, n_outputs=1)

    possible_inputs = list(product([True, False], repeat=2))
    expected_outputs = [gate_logic(a, b) for a, b in possible_inputs]

    for (a, b), expected_output in zip(possible_inputs, expected_outputs):
        result = simulator.simulate((a, b))
        if not result:
            assert False, "Simulation Failed"
        assert result == [expected_output]
