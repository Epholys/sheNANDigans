from typing import List
from circuit import Circuit

from simulator import Simulator
from wire_converter import convert_wires
from optimization_level import OptimizationLevel
from wire_extended_state import WireExtendedState


class SimulatorDebug(Simulator):
    """A simulator using a cautious approach to simulate a circuit."""

    def __init__(self, circuit: Circuit):
        super().__init__(circuit)
        convert_wires(self._circuit, OptimizationLevel.DEBUG)

    def _can_simulate(self, circuit: Circuit) -> bool:
        """Check if the circuit can be simulated, i.e. all inputs are determined."""
        return all(
            wire.state != WireExtendedState.UNKNOWN for wire in circuit.inputs.values()
        )

    def _simulate(self, circuit: Circuit) -> bool:
        """Simulate the circuit.

        The is a "debug" simulation, meaning it can only fails if the circuit
        is incorrect.

        Returns:
            bool: True if simulation completed successfully (all components simulated)
            False if simulation cannot proceed further.
        """
        # If the inputs are not set, we cannot simulate the circuit.
        if not self._can_simulate(circuit):
            return False

        # Base case: the circuit is a NAND gate.
        if circuit.identifier == 0:
            return self._simulate_nand(circuit)

        # Simulate all components.
        # We use a "light" brute-force approach by repeatedly trying to simulate
        # all components. A queue is used to remove from the components already
        # simulated.
        # This approach allows to simulate the circuit even if the components
        # are not defined in topological order.
        components_queue: List[Circuit] = list(circuit.components.values())
        left = len(components_queue)
        while True:
            to_simulate = left
            for _ in range(to_simulate):
                component = components_queue.pop(0)
                if not self._simulate(component):
                    components_queue.append(component)
            left = len(components_queue)

            if to_simulate == left:
                break

        # If there are still components to simulate, the simulation failed.
        return left == 0

    def _reset(self, circuit: Circuit):
        """Reset the wires to a initial UNKNOWN state."""
        for wire in circuit.inputs.values():
            wire.state = WireExtendedState.UNKNOWN

        for wire in circuit.outputs.values():
            wire.state = WireExtendedState.UNKNOWN

        for component in circuit.components.values():
            self._reset(component)
