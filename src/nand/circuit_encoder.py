from abc import ABC, abstractmethod
from bitarray import bitarray

from nand.circuits_library import CircuitLibrary


class CircuitEncoder(ABC):
    @abstractmethod
    def encode(self, library: CircuitLibrary) -> bitarray:
        pass
