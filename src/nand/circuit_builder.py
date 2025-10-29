from abc import ABC, abstractmethod
from nand.circuit import Circuit
from nand.circuit_library import CircuitLibrary
from nand.wire import Wire


class CircuitBuilder(ABC):
    def __init__(self):
        self.library = CircuitLibrary()

    def add_nand(self):
        nand_gate = Circuit(0)
        nand_gate.name = "NAND"
        nand_gate.inputs["A"] = Wire()
        nand_gate.inputs_names["A"] = "A"
        nand_gate.inputs["B"] = Wire()
        nand_gate.inputs_names["B"] = "B"
        nand_gate.outputs["OUT"] = Wire()
        nand_gate.outputs_names["OUT"] = "OUT"

        self.library.add_circuit(nand_gate)

    def add_zero(self):
        zero_gate = Circuit(1)
        zero_gate.name = "ZERO"
        zero_gate.outputs["OUT"] = Wire()
        zero_gate.outputs_names["OUT"] = "OUT"

        self.library.add_circuit(zero_gate)

    def add_one(self):
        one_gate = Circuit(2)
        one_gate.name = "ONE"
        one_gate.outputs["OUT"] = Wire()
        one_gate.outputs_names["OUT"] = "OUT"

        self.library.add_circuit(one_gate)

    @abstractmethod
    def build_circuits(self) -> CircuitLibrary:
        self.library.clear()
        self.add_nand()
        self.add_zero()
        self.add_one()
        return self.library
