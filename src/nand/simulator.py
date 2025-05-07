from typing import Literal, Sequence
from nand.circuit import Circuit
from abc import ABC, abstractmethod


type SimulationResult = Sequence[bool] | Literal[False]


class Simulator(ABC):
    """Abstract class for a circuit simulator.

    Attributes:
        _circuit: The circuit to simulate.
        _was_simulated: A flag indicating if the circuit was simulated.
    """

    def __init__(self, circuit: Circuit):
        self._circuit = circuit
        self._was_simulated = False

    def simulate(self, inputs: Sequence[bool]) -> SimulationResult:
        """Simulate the circuit with the given inputs.

        Args:
            inputs: The input values to simulate.

        Returns:
            The output values of the circuit if the simulation was successful,
            otherwise False.
        """
        # Reset the wires.
        self._reset(self._circuit)

        # Set the input values.
        for wire, input in zip(self._circuit.inputs.values(), inputs):
            wire.state = input

        # Simulate the circuit.
        if not self._simulate(self._circuit):
            return False

        self._was_simulated = True

        # Return the output values.
        return [bool(wire.state) for wire in list(self._circuit.outputs.values())]

    @abstractmethod
    def _reset(self, circuit: Circuit):
        """Reset the circuit before simulating it."""
        pass

    @abstractmethod
    def _simulate(self, circuit: Circuit) -> bool:
        """Simulate the circuit."""
        pass

    def _simulate_nand(self, nand: Circuit) -> bool:
        """Simulate the core NAND gate."""
        inputs = list(nand.inputs.values())
        a = inputs[0]
        b = inputs[1]
        out = list(nand.outputs.values())[0]
        out.state = not (a.state and b.state)
        return True

    def __str__(self):
        """Return a simple string representation of the simulator.

        Simply the name of the circuit, the simulation status, the inputs,
        and the outputs.
        """
        ins = "".join([str(wire) for wire in self._circuit.inputs.values()])
        outs = "".join([str(wire) for wire in self._circuit.outputs.values()])
        simulated = "simulated" if self._was_simulated else "not simulated"
        return f"{self._circuit.identifier} {simulated}: {ins} -> {outs}"

    def __repr__(self):
        """Return the complete detailed string representation of the simulator." """
        return (
            f"{type(self).__name__}(_was_simulated={self._was_simulated}, "
            f"circuit=\n {repr(self._circuit)})"
        )
