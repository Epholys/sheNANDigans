from simulator import Circuit, Simulator
from simulator_debug import SimulatorDebug
from simulator_fast import SimulatorFast
from optimization_level import OptimizationLevel


def build_simulator(circuit: Circuit, level: OptimizationLevel) -> Simulator:
    """Build a simulator according to the optimization level."""
    match level:
        case OptimizationLevel.DEBUG:
            return SimulatorDebug(circuit)
        case OptimizationLevel.FAST:
            return SimulatorFast(circuit)
        case _:
            raise ValueError("Unknown OptimizationLevel.")
