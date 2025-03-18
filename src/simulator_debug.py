from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from circuit import Circuit

from simulator import Simulator
from wire import WireExtendedState


class SimulatorDebug(Simulator):
    def __init__(self, circuit: Circuit):
        super().__init__()

    def _can_simulate(self, circuit: Circuit) -> bool:
        """Check if the circuit can be simulated, meaning that all inputs are determined."""
        return all(
            wire.state != WireExtendedState.UNKNOWN for wire in circuit.inputs.values()
        )

    def _was_simulated(self, circuit: Circuit) -> bool:
        """Check if the circuit was simulated, meaning that all outputs are determined."""
        return all(
            wire.state != WireExtendedState.UNKNOWN for wire in circuit.outputs.values()
        )

    def simulate(self, circuit: Circuit) -> bool:
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
        super().simulate(circuit)

        if not self._can_simulate(circuit) or self._was_simulated(circuit):
            return False

        if circuit.identifier == 0:
            self._simulate_nand(circuit)
            return True

        # There are much more "elegant" ways to do it (using any for example), but my brain
        # isn't python-wired enough to be sure to understand it tomorrow.
        while True:
            progress_made = False
            for component in circuit.components.values():
                if self.simulate(component):
                    progress_made = True

            if not progress_made:
                break

        return self._was_simulated(circuit)

    def reset(self, circuit: Circuit):
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

        self.components_stack = list(circuit.components.values())

        for component in circuit.components.values():
            self.reset(component)

    def debug_mode(self):
        pass
        # self.reset = self.reset_debug
        # self.simulate = self.simulate_slow
        # self.convert_wires_to_debug({})
