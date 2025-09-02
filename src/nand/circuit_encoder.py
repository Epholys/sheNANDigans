from abc import ABC, abstractmethod
from bitarray import bitarray

from nand.circuit_builder import CircuitLibrary


class CircuitEncoder(ABC):
    @abstractmethod
    def encode(self, library: CircuitLibrary) -> bitarray:
        pass
