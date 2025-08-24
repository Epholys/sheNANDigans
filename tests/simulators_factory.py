from enum import Enum
from typing import List, Tuple

from nand.default_decoder import DefaultDecoder
from nand.default_encoder import DefaultEncoder
from nand.bit_packed_decoder import BitPackedDecoder
from nand.optimization_level import OptimizationLevel
from nand.schematics import Schematics, SchematicsBuilder
from nand.simulator import Simulator
from nand.simulator_builder import build_simulator
from nand.bit_packed_encoder import BitPackedEncoder


class BuildProcess(Enum):
    """Enum to define the build process for the circuits."""

    REFERENCE = "reference"
    ROUND_TRIP = "round_trip"


class EncoderType(Enum):
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
        match self:
            case EncoderType.DEFAULT:
                return DefaultDecoder
            case EncoderType.BIT_PACKED:
                return BitPackedDecoder
            case _:
                raise ValueError("Unknown EncoderType.")


class SimulatorsFactory:
    def __init__(self) -> None:
        self._circuits: dict[Tuple[BuildProcess, EncoderType], Schematics] = {}
        self._simulators: dict[
            Tuple[BuildProcess, OptimizationLevel, EncoderType], List[Simulator]
        ] = {}

    def _build_circuits(self, encoder_type: EncoderType) -> None:
        """Build the circuits for the different build processes."""
        if BuildProcess.REFERENCE not in self._circuits:
            builder = SchematicsBuilder()
            builder.build_circuits()
            self._circuits[BuildProcess.REFERENCE, encoder_type] = builder.schematics

        if BuildProcess.ROUND_TRIP not in self._circuits:
            encoded = encoder_type.get_encoder().encode(
                self._circuits[BuildProcess.REFERENCE, encoder_type]
            )
            self._circuits[BuildProcess.ROUND_TRIP, encoder_type] = (
                encoder_type.get_decoder()(encoded).decode()
            )

    def get_simulators(
        self,
        build_kind: BuildProcess,
        optimization_level: OptimizationLevel,
        encoder_type: EncoderType = EncoderType.DEFAULT,
    ):
        """Get the simulators for the given build process and optimization level."""

        self._build_circuits(encoder_type)

        if (build_kind, optimization_level, encoder_type) not in self._simulators:
            schematics = self._circuits[build_kind, encoder_type]
            simulators = [
                build_simulator(circuit, optimization_level)
                for circuit in schematics.get_all_schematics().values()
            ]
            self._simulators[(build_kind, optimization_level, encoder_type)] = (
                simulators
            )

        return self._simulators[(build_kind, optimization_level, encoder_type)]
