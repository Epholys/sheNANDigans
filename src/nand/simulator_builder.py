from nand.circuit_optimizer import optimize
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

def build_fasts(circuit: Circuit) -> list[SimulatorFast]:
    return [SimulatorFast(optimized, already_optimized=True) for optimized in optimize(circuit, multiple=True)]