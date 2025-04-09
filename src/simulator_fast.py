from circuit import Circuit
from simulator import Simulator
from wire_converter import convert_wires
from circuit_optimizer import optimize
from optimization_level import OptimizationLevel


class SimulatorFast(Simulator):
    """A simulator that does not have any caution.

    To do so, it assumes the circuit is correctly defined. If this is not the case,
    the simulation will produce wrong results.
    """

    def __init__(self, circuit: Circuit):
        super().__init__(circuit)

        # Optimize the circuit to put it in a topological order.
        optimize(self._circuit)

        convert_wires(self._circuit, OptimizationLevel.FAST)

    def _simulate(self, circuit: Circuit):
        """Simulate the circuit.

        The is a "fast" simulation, meaning it assumes the circuit is correct
        (no loop / missing connections / etc).

        Returns:
            bool: systematically True: there's no check of simulation failure.
        """
        # Base case: the circuit is a NAND gate.
        if circuit.identifier == 0:
            self._simulate_nand(circuit)
            return True

        # The components are supposed to be in topological order, so a simple
        # loop is enough.
        for component in circuit.components.values():
            self._simulate(component)

        return True

    def _reset(self, circuit: Circuit):
        """noop: only the inputs are set before simulating."""
        pass
