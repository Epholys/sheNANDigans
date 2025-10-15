from abc import ABC, abstractmethod

from nand.circuit import Circuit, Wire
from nand.circuit_builder import CircuitLibrary
from nand.circuit_encoder import BitArrayLike


class CircuitDecoder(ABC):
    @abstractmethod
    def decode(self, data: BitArrayLike) -> CircuitLibrary:
        pass

    def _build_core_gates(self, library: CircuitLibrary):
        library.add_circuit(self._build_nand())
        library.add_circuit(self._build_zero())
        library.add_circuit(self._build_one())

    def _build_nand(self) -> Circuit:
        nand_gate = Circuit(0)
        nand_gate.inputs[0] = Wire()
        nand_gate.inputs_names[0] = "A"
        nand_gate.inputs[1] = Wire()
        nand_gate.inputs_names[1] = "B"
        nand_gate.outputs[0] = Wire()
        nand_gate.outputs_names[0] = "OUT"
        return nand_gate

    def _build_zero(self) -> Circuit:
        zero_gate = Circuit(1)
        zero_gate.outputs[0] = Wire()
        zero_gate.outputs_names[0] = "0"
        return zero_gate

    def _build_one(self) -> Circuit:
        one_gate = Circuit(2)
        one_gate.outputs[0] = Wire()
        one_gate.outputs_names[0] = "1"
        return one_gate
