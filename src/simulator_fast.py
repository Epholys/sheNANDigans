from wire import WireFast
from circuit import Circuit
from simulator import Simulator
from circuit_converter import convert_wires


class SimulatorFast(Simulator):
    def __init__(self, circuit: Circuit):
        super().__init__(circuit)

        if self.circuit.is_debug:
            convert_wires(self.circuit, WireFast)
            self.circuit.is_debug = False

    def simulate(self, circuit: Circuit):
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

        if circuit.identifier == 0:
            self._simulate_nand(circuit)
            return True

        # There are much more "elegant" ways to do it (using any for example), but my brain
        # isn't python-wired enough to be sure to understand it tomorrow.
        for component in circuit.components.values():
            self.simulate(component)

        return True

    def reset(self, circuit: Circuit):
        pass
