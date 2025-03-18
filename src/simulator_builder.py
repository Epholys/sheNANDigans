from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from circuit import Circuit

from enum import Enum, auto
from typing import Type
from simulator import Simulator
from simulator_debug import SimulatorDebug
from simulator_fast import SimulatorFast
from wire import Wire, WireDebug, WireFast


class OptimizationLevel(Enum):
    DEBUG = auto()
    FAST = auto()


def get_wire_class(level: OptimizationLevel) -> Type[Wire]:
    match level:
        case OptimizationLevel.DEBUG:
            return WireDebug
        case OptimizationLevel.FAST:
            return WireFast
        case _:
            raise ValueError("Unknown OptimizationLevel.")


def build_simulator(circuit: Circuit, level: OptimizationLevel) -> Simulator:
    match level:
        case OptimizationLevel.DEBUG:
            return SimulatorDebug(circuit)
        case OptimizationLevel.FAST:
            return SimulatorFast(circuit)
        case _:
            raise ValueError("Unkonwn OptimizationLevel.")
