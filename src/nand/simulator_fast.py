from nand.circuit import Circuit
from nand.simulator import Simulator
from nand.wire_converter import convert_wires
from nand.circuit_optimizer import optimize
from nand.optimization_level import OptimizationLevel


class SimulatorFast(Simulator):
    """A simulator that does not have any caution.

    To do so, it assumes the circuit is correctly defined. If this is not the case,
    the simulation will produce wrong results.

    # TODO optimize() : mark circuit as optimized to avoid repetition?
    # TODO : create a new SimulatorFlattened, or add flat to this SimulatorFast?
    """

    def __init__(self, circuit: Circuit):
        super().__init__(circuit)

        # Optimize the circuit to put it in a topological order.
        optimize(self._circuit)

        convert_wires(self._circuit, OptimizationLevel.FAST)

    def _simulate(self, circuit: Circuit):
        """Simulate the circuit.

        This is a "fast" simulation, meaning it assumes the circuit is correct
        (no loop / missing connections / etc).

        Returns:
            bool: systematically True: there's no check of simulation failure.
        """
        # Base case: the circuit is a core gate.
        if self._is_core_gate(circuit):
            self._simulate_core_gate(circuit)
            return True

        # The components are supposed to be in topological order, so a simple
        # loop is enough.
        for component in circuit.components.values():
            self._simulate(component)

        return True

    def _reset(self, circuit: Circuit):
        """noop: only the inputs are set before simulating."""
        pass
