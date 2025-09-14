from copy import deepcopy
from typing import OrderedDict
from nand.circuit import Circuit, CircuitDict, CircuitId


class CircuitLibrary:
    """Circuit container wrapper.

    Its main goal is to deepcopy the circuit queried when building and d/encoding.
    Otherwise, every component of a type of circuit (like XOR for example) would be a
    single object, which wreaks havoc everywhere.
    """

    def __init__(self):
        self._circuits: CircuitDict = OrderedDict()

    def has_circuit(self, identifier: CircuitId):
        return identifier in self._circuits

    def add_circuit(self, circuit: Circuit):
        if self.has_circuit(circuit.identifier):
            raise ValueError(f"Circuit {circuit.identifier} already exists")

        self._circuits[circuit.identifier] = circuit

    def get_circuit(self, identifier: CircuitId) -> Circuit:
        if not self.has_circuit(identifier):
            raise ValueError(f"Circuit {identifier} does not exist")
        return deepcopy(self._circuits[identifier])

    def get_all_circuits(self) -> CircuitDict:
        return {k: deepcopy(circuit) for k, circuit in self._circuits.items()}

    def get_circuit_from_idx(self, idx: int) -> Circuit:
        try:
            circuit: Circuit = list(self._circuits.values())[idx]
        except IndexError as e:
            raise ValueError(f"Circuit of index {idx} does not exist") from e
        return deepcopy(circuit)

    def clear(self):
        self._circuits.clear()

    def __len__(self):
        return len(self._circuits)
