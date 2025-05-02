from typing import List, Optional

from src.decoding import CircuitDecoder
from src.encoding import CircuitEncoder
from src.optimization_level import OptimizationLevel
from src.schematics import Schematics, SchematicsBuilder
from src.simulator import Simulator
from src.simulator_builder import build_simulator


class TestedCircuits:
    reference: Optional[Schematics] = None
    round_trip: Optional[Schematics] = None


class Simulators:
    reference: List[Simulator] = []
    round_trip: List[Simulator] = []


circuits = TestedCircuits()
simulators_fast = Simulators()
simulators_debug = Simulators()


def build_simulators(processing: str, optimization_level: OptimizationLevel):
    global circuits
    global simulators_fast
    global simulators_debug

    if optimization_level == OptimizationLevel.FAST:
        simulators = simulators_fast
    elif optimization_level == OptimizationLevel.DEBUG:
        simulators = simulators_debug
    else:
        raise TypeError("Unknown OptimizationLevel.")

    if circuits.reference is None:
        builder = SchematicsBuilder()
        builder.build_circuits()
        circuits.reference = builder.schematics
    if circuits.round_trip is None:
        encoded = CircuitEncoder(circuits.reference).encode()
        circuits.round_trip = CircuitDecoder(encoded).decode()

    if processing != "reference" and processing != "round_trip":
        raise ValueError("Unknown schematics request.")

    if processing == "reference" and len(simulators.reference) == 0:
        simulators.reference = [
            build_simulator(circuit, optimization_level)
            for circuit in circuits.reference.get_all_schematics().values()
        ]
    if processing == "round_trip" and len(simulators.round_trip) == 0:
        simulators.round_trip = [
            build_simulator(circuit, optimization_level)
            for circuit in circuits.round_trip.get_all_schematics().values()
        ]


def choose_simulators(
    processing: str, optimization_level: OptimizationLevel
) -> List[Simulator]:
    global simulators_fast
    global simulators_debug

    if optimization_level == OptimizationLevel.FAST:
        simulators = simulators_fast
    elif optimization_level == OptimizationLevel.DEBUG:
        simulators = simulators_debug
    else:
        raise TypeError("Unknown OptimizationLevel.")

    build_simulators(processing, optimization_level)

    if processing == "reference":
        return simulators.reference
    elif processing == "round_trip":
        return simulators.round_trip
    else:
        raise ValueError("Unknown schematics request.")
