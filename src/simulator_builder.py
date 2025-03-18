from circuit import Circuit
from simulator import Simulator
from simulator_debug import SimulatorDebug
from simulator_fast import SimulatorFast


def build_simulator(circuit: Circuit) -> Simulator:
    if circuit.is_debug:
        return SimulatorDebug(circuit)
    else:
        return SimulatorFast(circuit)
