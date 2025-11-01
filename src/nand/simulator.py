from typing import List, Literal, Sequence
from nand.circuit import Circuit
from abc import ABC, abstractmethod


type SimulationResult = List[bool] | Literal[False]


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

        print(f"==simulate circuit {self._circuit.name}==")
        print(f"components : {[comp.identifier for comp in self._circuit.components.values()]}")
        print(f"circuit inputs: {self._circuit.get_input_wires()}")
        print(f"simulation inputs: {inputs}")

        # Set the input values.
        for wire, input_ in zip(self._circuit.get_input_wires(), inputs):
            wire.state = input_

        print(f"inputs are sets: {self._circuit.get_input_wires()}")

        # Simulate the circuit.
        if not self._simulate(self._circuit):
            return False

        self._was_simulated = True

        # Return the output values.
        return [bool(wire.state) for wire in list(self._circuit.get_output_wires())]

    @abstractmethod
    def _reset(self, circuit: Circuit):
        """Reset the circuit before simulating it."""
        pass

    @abstractmethod
    def _simulate(self, circuit: Circuit) -> bool:
        """Simulate the circuit."""
        pass

    def _simulate_nand(self, nand: Circuit):
        """Simulate the core NAND gate."""
        inputs = nand.get_input_wires()
        print(f"nand: {repr(nand)}")
        print(f"nand inputs: {inputs}")
        a = inputs[0]
        b = inputs[1]
        out = nand.get_output_wires()[0]
        print(f"out: {repr(out)}")
        out.state = not (a.state and b.state)
        print(f"out.state: {repr(out.state)}")
        print(nand.get_input_wires())
        print(nand.get_output_wires())

    def _simulate_zero(self, zero: Circuit):
        """Simulate the core ZERO gate."""
        out = zero.get_output_wires()[0]
        out.state = False

    def _simulate_one(self, one: Circuit):
        """Simulate the core ONE gate."""
        out = one.get_output_wires()[0]
        out.state = True

    def _simulate_core_gate(self, circuit: Circuit):
        """Simulate the core gates."""
        if circuit.identifier == 0:
            self._simulate_nand(circuit)
        elif circuit.identifier == 1:
            self._simulate_zero(circuit)
        elif circuit.identifier == 2:
            self._simulate_one(circuit)
        else:
            raise ValueError(f"Unknown core circuit identifier: {circuit.identifier}")

    def _is_core_gate(self, circuit: Circuit) -> bool:
        """Check if the circuit is a core gate."""
        match circuit.identifier:
            case 0 | 1 | 2:
                return True
            case _:
                return False

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
