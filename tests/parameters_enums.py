from enum import Enum
from typing import Any

from nand.bit_packed_decoder import BitPackedDecoder
from nand.bit_packed_encoder import BitPackedEncoder
from nand.default_decoder import DefaultDecoder
from nand.default_encoder import DefaultEncoder
from nand.flattened_circuit_builder import FlattenedCircuitBuilder
from nand.nand2tetris_hack_alu import HackALUBuilder
from nand.playground_circuit_builder import PlaygroundCircuitBuilder


class BuildProcess(Enum):
    """Enum to define the build process for the circuits."""

    REFERENCE = "reference"
    ROUND_TRIP = "round_trip"


class EncoderAlgorithm(Enum):
    """Enum defining all D/Encoders available."""

    DEFAULT = "default"
    BIT_PACKED = "bit_packed"

    def get_encoder(self):
        # TODO : Type[] because non-stateless decoder, see other TODO
        match self:
            case EncoderAlgorithm.DEFAULT:
                return DefaultEncoder
            case EncoderAlgorithm.BIT_PACKED:
                return BitPackedEncoder
            case _:
                raise ValueError("Unknown EncoderType.")

    def get_decoder(self):
        # TODO : Type[] because non-stateless decoder, see other TODO
        match self:
            case EncoderAlgorithm.DEFAULT:
                return DefaultDecoder
            case EncoderAlgorithm.BIT_PACKED:
                return BitPackedDecoder
            case _:
                raise ValueError("Unknown EncoderType.")


class Project(Enum):
    """Enum defining all projects, i.e. all circuit libraries."""

    PLAYGROUND = "playground"
    NAND2TETRIS_HACK = "nand2tetris_hack"
    PLAYGROUND_FLATTENED = "playground_flattened"
    NAND2TETRIS_HACK_FLATTENED = "nand2tetris_hack_flattened"

    def get_builder(self):
        match self:
            case Project.PLAYGROUND:
                return PlaygroundCircuitBuilder()
            case Project.NAND2TETRIS_HACK:
                return HackALUBuilder()
            case Project.PLAYGROUND_FLATTENED:
                return FlattenedCircuitBuilder(PlaygroundCircuitBuilder)
            case Project.NAND2TETRIS_HACK_FLATTENED:
                return FlattenedCircuitBuilder(HackALUBuilder)
            case _:
                raise ValueError("Unknown Project.")


def parameter_ids(parameters: Any):
    """Function to pretty-print cases for parametrized tests"""
    match parameters:
        case tuple():
            return " - ".join([parameter_ids(params) for params in parameters])
        case Enum():
            return parameters.name
        case _:
            return str(parameters)
