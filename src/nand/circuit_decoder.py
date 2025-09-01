from abc import ABC, abstractmethod
from bitarray import bitarray

from nand.circuit import Circuit, Wire
from nand.schematics import Schematics


class CircuitDecoder(ABC):
    @abstractmethod
    def decode(self, data: bitarray) -> Schematics:
        pass

    def _build_nand(self) -> Circuit:
        nand_gate = Circuit(0)
        nand_gate.inputs[0] = Wire()
        nand_gate.inputs_names[0] = "0"
        nand_gate.inputs[1] = Wire()
        nand_gate.inputs_names[1] = "1"
        nand_gate.outputs[0] = Wire()
        nand_gate.outputs_names[0] = "0"
        return nand_gate
