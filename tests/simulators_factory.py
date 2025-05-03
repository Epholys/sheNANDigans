from enum import Enum
from typing import List, Tuple

from src.decoding import CircuitDecoder
from src.encoding import CircuitEncoder
from src.optimization_level import OptimizationLevel
from src.schematics import Schematics, SchematicsBuilder
from src.simulator import Simulator
from src.simulator_builder import build_simulator


class BuildProcess(Enum):
    """Enum to define the build process for the circuits."""

    REFERENCE = "reference"
    ROUND_TRIP = "round_trip"


class SimulatorsFactory:
    def __init__(self) -> None:
        self._circuits: dict[BuildProcess, Schematics] = {}
        self._simulators: dict[
            Tuple[BuildProcess, OptimizationLevel], List[Simulator]
        ] = {}

    def _build_circuits(self) -> None:
        """Build the circuits for the different build processes."""
        if BuildProcess.REFERENCE not in self._circuits:
            builder = SchematicsBuilder()
            builder.build_circuits()
            self._circuits[BuildProcess.REFERENCE] = builder.schematics

        if BuildProcess.ROUND_TRIP not in self._circuits:
            encoded = CircuitEncoder(self._circuits[BuildProcess.REFERENCE]).encode()
            self._circuits[BuildProcess.ROUND_TRIP] = CircuitDecoder(encoded).decode()

    def get_simulators(
        self, build_kind: BuildProcess, optimization_level: OptimizationLevel
    ):
        """Get the simulators for the given build process and optimization level."""

        self._build_circuits()

        if (build_kind, optimization_level) not in self._simulators:
            schematics = self._circuits[build_kind]
            simulators = [
                build_simulator(circuit, optimization_level)
                for circuit in schematics.get_all_schematics().values()
            ]
            self._simulators[(build_kind, optimization_level)] = simulators

        return self._simulators[(build_kind, optimization_level)]
