from typing import Type

from nand.circuit_builder import CircuitBuilder
from nand.flattener import flatten_circuit
from nand.nand2tetris_hack_alu import HackALUBuilder
from nand.playground_circuit_builder import PlaygroundCircuitBuilder


class FlattenedCircuitBuilder(CircuitBuilder):
    def __init__(self, builder: Type[CircuitBuilder]):
        super().__init__()
        self.builder = builder

    def build_circuits(self):
        library = self.builder().build_circuits()
        for circuit in library.get_all_circuits().values():
            self.library.add_circuit(flatten_circuit(circuit))
        return self.library

class FlattenedPlaygroundCircuitBuilder(FlattenedCircuitBuilder):
    def __init__(self):
        super().__init__(PlaygroundCircuitBuilder)

    def build_circuits(self):
        return super().build_circuits()

class FlattenedHackALUBuilder(FlattenedCircuitBuilder):
    def __init__(self):
        super().__init__(HackALUBuilder)

    def build_circuits(self):
        return super().build_circuits()


