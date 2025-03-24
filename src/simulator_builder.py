from simulator import Circuit, Simulator
from simulator_debug import SimulatorDebug
from simulator_fast import SimulatorFast
from src.optimization_level import OptimizationLevel


def build_simulator(circuit: Circuit, level: OptimizationLevel) -> Simulator:
    match level:
        case OptimizationLevel.DEBUG:
            return SimulatorDebug(circuit)
        case OptimizationLevel.FAST:
            return SimulatorFast(circuit)
        case _:
            raise ValueError("Unknown OptimizationLevel.")
