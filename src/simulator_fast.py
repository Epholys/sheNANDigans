from circuit import Circuit
from simulator import Simulator
from circuit_converter import set_wires
from src.circuit_optimizer import optimize
from src.optimization_level import OptimizationLevel


class SimulatorFast(Simulator):
    def __init__(self, circuit: Circuit):
        super().__init__(circuit)
        optimize(self.circuit)
        set_wires(self.circuit, OptimizationLevel.FAST)

    def _simulate(self, circuit: Circuit):
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
        if circuit.identifier == 0:
            self._simulate_nand(circuit)
            return True

        # There are much more "elegant" ways to do it (using any for example), but my brain
        # isn't python-wired enough to be sure to understand it tomorrow.
        for component in circuit.components.values():
            self._simulate(component)

        return True

    def _reset(self, circuit: Circuit):
        pass
