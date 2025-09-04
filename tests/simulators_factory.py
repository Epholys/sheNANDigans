from enum import Enum
import itertools
from typing import List, Tuple

import pytest

from nand.default_decoder import DefaultDecoder
from nand.default_encoder import DefaultEncoder
from nand.bit_packed_decoder import BitPackedDecoder
from nand.nand2tetris_hack_alu import HackALUBuilder
from nand.optimization_level import OptimizationLevel
from nand.circuit_builder import CircuitLibrary
from nand.simulator import Simulator
from nand.simulator_builder import build_simulator
from nand.bit_packed_encoder import BitPackedEncoder
from nand.playground_circuit_builder import PlaygroundCircuitBuilder


class BuildProcess(Enum):
    """Enum to define the build process for the circuits."""

    REFERENCE = "reference"
    ROUND_TRIP = "round_trip"


class EncoderType(Enum):
    """Enum defining all D/Encoders available."""

    DEFAULT = "default"
    BIT_PACKED = "bit_packed"

    def get_encoder(self):
        match self:
            case EncoderType.DEFAULT:
                return DefaultEncoder()
            case EncoderType.BIT_PACKED:
                return BitPackedEncoder()
            case _:
                raise ValueError("Unknown EncoderType.")

    def get_decoder(self):
        # TODO : Type[] because non-stateless decoder, see other TODO
        match self:
            case EncoderType.DEFAULT:
                return DefaultDecoder
            case EncoderType.BIT_PACKED:
                return BitPackedDecoder
            case _:
                raise ValueError("Unknown EncoderType.")


class Project(Enum):
    """Enum defining all projects, i.e. all circuit libraries."""

    PLAYGROUND = "playground"
    NAND2TETRIS_HACK = "nand2tetris_hack"

    def get_builder(self):
        match self:
            case Project.PLAYGROUND:
                return PlaygroundCircuitBuilder()
            case Project.NAND2TETRIS_HACK:
                return HackALUBuilder()
            case _:
                raise ValueError("Unknown Project.")


def build_parameters(project: Project):
    """Build the parameters for the tests.

    The parameters are a combination of:
    - BuildProcess: REFERENCE, ROUND_TRIP
    - OptimizationLevel: FAST, DEBUG
    - EncoderType: DEFAULT, BIT_PACKED

    With 'project' being a parameter to separate each library tested.

    The DEBUG optimization level is marked as 'debug' to be able to run it
    separately.
    """
    params = []

    processes = [BuildProcess.REFERENCE, BuildProcess.ROUND_TRIP]
    opt_levels = [OptimizationLevel.FAST, OptimizationLevel.DEBUG]
    encoders = [EncoderType.DEFAULT, EncoderType.BIT_PACKED]
    for p, o, e in itertools.product(processes, opt_levels, encoders):
        mark_debug = pytest.mark.debug if o is OptimizationLevel.DEBUG else None
        if mark_debug:
            params.append(pytest.param((p, o, e, project), marks=mark_debug))
        else:
            params.append(pytest.param((p, o, e, project)))
    return params


class SimulatorsFactory:
    def __init__(self) -> None:
        self._circuits: dict[Tuple[BuildProcess, EncoderType], CircuitLibrary] = {}
        self._simulators: dict[
            Tuple[BuildProcess, OptimizationLevel, EncoderType], List[Simulator]
        ] = {}

    def _build_circuits(self, encoder_type: EncoderType, project: Project) -> None:
        """Build the circuits for the different build processes."""
        if BuildProcess.REFERENCE not in self._circuits:
            builder = project.get_builder()
            builder.build_circuits()
            self._circuits[BuildProcess.REFERENCE, encoder_type] = builder.library

        if BuildProcess.ROUND_TRIP not in self._circuits:
            encoded = encoder_type.get_encoder().encode(
                self._circuits[BuildProcess.REFERENCE, encoder_type]
            )
            self._circuits[BuildProcess.ROUND_TRIP, encoder_type] = (
                encoder_type.get_decoder()().decode(encoded)
            )

    def get_simulators(
        self,
        build_kind: BuildProcess,
        optimization_level: OptimizationLevel,
        encoder_type: EncoderType = EncoderType.DEFAULT,
        project: Project = Project.PLAYGROUND,
    ):
        """Get the simulators for the given build process and optimization level."""

        self._build_circuits(encoder_type, project)

        if (build_kind, optimization_level, encoder_type) not in self._simulators:
            library = self._circuits[build_kind, encoder_type]
            simulators = [
                build_simulator(circuit, optimization_level)
                for circuit in library.get_all_circuits().values()
            ]
            self._simulators[(build_kind, optimization_level, encoder_type)] = (
                simulators
            )

        return self._simulators[(build_kind, optimization_level, encoder_type)]
