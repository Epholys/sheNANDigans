from enum import Enum, auto
from typing import Sequence
from circuit import Circuit
from abc import ABC, abstractmethod


class SimulationErrorCode(Enum):
    SIZE_MISMATCH = auto()
    SIMULATION_FAILURE = auto()


type SimulationResult = Sequence[bool] | SimulationErrorCode


class Simulator(ABC):
    def __init__(self, circuit: Circuit):
        self.circuit = circuit

    def simulate(self, inputs: Sequence[bool], n_outputs: int) -> SimulationResult:
        if not self._check_size(len(inputs), n_outputs):
            return SimulationErrorCode.SIZE_MISMATCH

        self._reset(self.circuit)

        for wire, input in zip(self.circuit.inputs.values(), inputs):
            wire.state = input

        if not self._simulate(self.circuit):
            return SimulationErrorCode.SIMULATION_FAILURE

        return [bool(wire.state) for wire in list(self.circuit.outputs.values())]

    @abstractmethod
    def _reset(self, circuit: Circuit):
        pass

    @abstractmethod
    def _simulate(self, circuit: Circuit) -> bool:
        pass

    def _simulate_nand(self, nand: Circuit) -> bool:
        """Simulate a NAND gate"""
        inputs = list(nand.inputs.values())
        a = inputs[0]
        b = inputs[1]
        out = list(nand.outputs.values())[0]
        out.state = not (a.state and b.state)
        return True

    def _check_size(self, n_inputs: int, n_outputs: int) -> bool:
        return (
            len(self.circuit.inputs) == n_inputs
            and len(self.circuit.outputs) == n_outputs
        )
