from itertools import product
from typing import Callable, Union
from nand.circuit import Circuit
from nand.simulator import Simulator


def assert_circuit_signature(circuit: Circuit, n_inputs: int, n_outputs: int):
    """Assert the signature of a circuit (number of inputs and outputs)."""
    assert len(circuit.inputs) == n_inputs
    assert len(circuit.outputs) == n_outputs


def _assert_logic_gate_simulations(
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


BoolFunc = Union[
    Callable[[bool], bool],
    Callable[[bool, bool], bool],
    Callable[[bool, bool, bool], bool],
    Callable[[bool, bool, bool, bool], bool],
    # Add as many as you need
]


def tttassert(simulator: Simulator, gate_logic: BoolFunc, n_in: int):
    """Assert the simulation of a logic gate.
    'gate_logic' is the expected behavior of the gate.
    """
    assert_circuit_signature(simulator._circuit, n_inputs=n_in, n_outputs=1)

    possible_inputs = list(product([True, False], repeat=n_in))
    expected_outputs = [gate_logic(*ins) for ins in possible_inputs]

    for ins, expected_output in zip(possible_inputs, expected_outputs):
        result = simulator.simulate(ins)
        if not result:
            assert False, "Simulation Failed"
        assert result == [expected_output]


def assert_logic_gate_simulations(simulator: Simulator, gate_logic: BoolFunc):
    """Assert the simulation of a logic gate.
    'gate_logic' is the expected behavior of the gate.
    """
    tttassert(simulator, gate_logic, 2)
