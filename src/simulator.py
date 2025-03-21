from typing import Literal, Sequence
from circuit import Circuit
from abc import ABC, abstractmethod


type SimulationResult = Sequence[bool] | Literal[False]


class Simulator(ABC):
    """_summary_

    TODO : Tell about NAND

    Args:
        ABC (_type_): _description_
    """

    def __init__(self, circuit: Circuit):
        self._circuit = circuit
        self._was_simulated = False

    def simulate(self, inputs: Sequence[bool]) -> SimulationResult:
        self._reset(self._circuit)

        for wire, input in zip(self._circuit.inputs.values(), inputs):
            wire.state = input

        if not self._simulate(self._circuit):
            return False

        self._was_simulated = True

        return [bool(wire.state) for wire in list(self._circuit.outputs.values())]

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
            len(self._circuit.inputs) == n_inputs
            and len(self._circuit.outputs) == n_outputs
        )

    def __str__(self):
        ins = "".join([str(wire) for wire in self._circuit.inputs.values()])
        outs = "".join([str(wire) for wire in self._circuit.outputs.values()])
        simulated = "simulated" if self._was_simulated else "not simulated"
        return f"{self._circuit.identifier} {simulated}: {ins} -> {outs}"

    def __repr__(self):
        return (
            f"{type(self).__name__}(_was_simulated={self._was_simulated}, "
            f"circuit=\n {repr(self._circuit)})"
        )
