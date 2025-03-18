from abc import ABC, abstractmethod
from circuit import Circuit


class Simulator(ABC):
    def __init__(self, circuit: Circuit):
        self.circuit = circuit

    @abstractmethod
    def reset(self, circuit: Circuit):
        pass

    @abstractmethod
    def simulate(self, circuit: Circuit) -> bool:
        self.reset(circuit)
        pass

    def _simulate_nand(self, nand: Circuit):
        """Simulate a NAND gate"""
        inputs = list(nand.inputs.values())
        a = inputs[0]
        b = inputs[1]
        out = list(nand.outputs.values())[0]
        out.state = not (a.state and b.state)
