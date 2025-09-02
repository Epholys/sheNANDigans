from copy import deepcopy
from typing import OrderedDict
from nand.circuit import Circuit, CircuitDict, CircuitId


class CircuitLibrary:
    def __init__(self):
        self.library: CircuitDict = OrderedDict()

    def has_circuit(self, identifier: CircuitId):
        return identifier in self.library

    def add_circuit(self, circuit: Circuit):
        if self.has_circuit(circuit.identifier):
            raise ValueError(f"Circuit {circuit.identifier} already exists")

        self.library[circuit.identifier] = circuit

    def get_circuit(self, identifier: CircuitId) -> Circuit:
        if not self.has_circuit(identifier):
            raise ValueError(f"Circuit {identifier} does not exist")
        return deepcopy(self.library[identifier])

    def get_all_circuits(self) -> CircuitDict:
        return {k: deepcopy(circuit) for k, circuit in self.library.items()}

    def get_circuit_from_idx(self, idx: int) -> Circuit:
        try:
            circuit: Circuit = list(self.library.values())[idx]
        except IndexError as e:
            raise ValueError(f"Circuit of index {idx} does not exist") from e
        return deepcopy(circuit)
