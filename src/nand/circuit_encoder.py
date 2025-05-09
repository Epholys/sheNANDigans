from abc import ABC, abstractmethod
from bitarray import bitarray

from nand.schematics import Schematics


class CircuitEncoder(ABC):
    @abstractmethod
    def encode(self, library: Schematics) -> bitarray:
        pass
