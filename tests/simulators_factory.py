from dataclasses import dataclass
import itertools
from typing import List

import pytest

from tests.circuits_factory import CircuitSpecs, CircuitsFactory
from nand.optimization_level import OptimizationLevel
from nand.simulator import Simulator
from nand.simulator_builder import build_simulator
from tests.parameters_enums import BuildProcess, EncoderAlgorithm, Project


@dataclass(frozen=True)
class SimulatorSpecs:
    """Specification defining a simulator kind to tests."""

    build_process: BuildProcess
    encoder_algorithm: EncoderAlgorithm
    project: Project
    optimization_level: OptimizationLevel


def build_simulators_cases(project: Project):
    """Build the parameters for the tests.

    The parameters are a combination of, BuildProcess, EncoderAlgorithm,
    and OptimizationLevel. Their enum defines all cases.

    With 'project' being a parameter to separate each library tested.

    The DEBUG optimization level is marked as 'debug' to be able to run it
    separately.
    """
    params = []
    for process, algo, opt in itertools.product(
        BuildProcess, EncoderAlgorithm, OptimizationLevel
    ):
        mark_debug = pytest.mark.debug if opt is OptimizationLevel.DEBUG else None
        if mark_debug:
            params.append(pytest.param((process, algo, project, opt), marks=mark_debug))
        else:
            params.append(pytest.param((process, algo, project, opt)))
    return params


class SimulatorsFactory:
    def __init__(self) -> None:
        self._simulators: dict[SimulatorSpecs, List[Simulator]] = {}

    def get_simulators(
        self, specs: SimulatorSpecs, circuits_factory: CircuitsFactory
    ) -> List[Simulator]:
        """Get the simulators for a given specification."""

        circuit_spec = CircuitSpecs(
            specs.build_process, specs.encoder_algorithm, specs.project
        )

        library = circuits_factory.get_circuits(circuit_spec)

        if specs not in self._simulators:
            simulators = [
                build_simulator(circuit, specs.optimization_level)
                for circuit in library.get_all_circuits().values()
            ]
            self._simulators[specs] = simulators

        return self._simulators[specs]
