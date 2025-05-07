from nand.simulator import Circuit, Simulator
from nand.simulator_debug import SimulatorDebug
from nand.simulator_fast import SimulatorFast
from nand.optimization_level import OptimizationLevel


def build_simulator(circuit: Circuit, level: OptimizationLevel) -> Simulator:
    """Build a simulator according to the optimization level."""
    match level:
        case OptimizationLevel.DEBUG:
            return SimulatorDebug(circuit)
        case OptimizationLevel.FAST:
            return SimulatorFast(circuit)
        case _:
            raise ValueError("Unknown OptimizationLevel.")
