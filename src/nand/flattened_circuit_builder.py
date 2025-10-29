from typing import Type

from nand.circuit_builder import CircuitBuilder
from nand.flattener import flatten_circuit


class FlattenedCircuitBuilder(CircuitBuilder):
    def __init__(self, builder: Type[CircuitBuilder]):
        super().__init__()
        self.builder = builder

    def build_circuits(self):
        library = self.builder().build_circuits()
        for circuit in library.get_all_circuits().values():
            self.library.add_circuit(flatten_circuit(circuit))
        return self.library
