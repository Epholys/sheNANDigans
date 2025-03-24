from typing import List
from circuit import Circuit

from simulator import Simulator
from src.wire_converter import convert_wires
from optimization_level import OptimizationLevel
from wire import WireExtendedState


class SimulatorDebug(Simulator):
    def __init__(self, circuit: Circuit):
        super().__init__(circuit)
        convert_wires(self._circuit, OptimizationLevel.DEBUG)

    def _can_simulate(self, circuit: Circuit) -> bool:
        """Check if the circuit can be simulated, meaning that all inputs are determined."""
        return all(
            wire.state != WireExtendedState.UNKNOWN for wire in circuit.inputs.values()
        )

    def _simulate(self, circuit: Circuit) -> bool:
        """
        Simulate the circuit's behavior.

        Performs digital logic simulation by either:
        1. For NAND gates (identifier=0): Directly computes NAND logic
        2. For complex circuits: Iteratively simulates sub-components until either:
           - All outputs are determined (success)
           - Or no further progress can be made (deadlock)

        Returns:
            bool: True if simulation completed successfully (all outputs determined)
                 False if simulation cannot proceed or is already complete

        Note:
            Increments self.miss counter when sub-component simulation fails
        """
        if not self._can_simulate(circuit):
            return False

        if circuit.identifier == 0:
            return self._simulate_nand(circuit)

        components_queue: List[Circuit] = list(circuit.components.values())
        left = len(components_queue)
        while True:
            to_simulate: int = left
            for _ in range(to_simulate):
                component = components_queue.pop(0)
                if not self._simulate(component):
                    components_queue.append(component)
            left = len(components_queue)

            if to_simulate == left:
                break

        return left == 0

    def _reset(self, circuit: Circuit):
        """
        Reset the circuit to its initial state.

        Resets:
        - All wires' state to Unknown
        - All components recursively
        - The simulation miss counter
        """
        for wire in circuit.inputs.values():
            wire.state = WireExtendedState.UNKNOWN

        for wire in circuit.outputs.values():
            wire.state = WireExtendedState.UNKNOWN

        for component in circuit.components.values():
            self._reset(component)
