from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from circuit import Circuit

from abc import ABC, abstractmethod


class Simulator(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def reset(self, circuit: Circuit):
        pass

    @abstractmethod
    def simulate(self, circuit: Circuit) -> bool:
        pass

    def _simulate_nand(self, nand: Circuit):
        """Simulate a NAND gate"""
        inputs = list(nand.inputs.values())
        a = inputs[0]
        b = inputs[1]
        out = list(nand.outputs.values())[0]
        out.state = not (a.state and b.state)
