from abc import ABC, abstractmethod
from bitarray import bitarray

from nand.schematics import Schematics


class CircuitDecoder(ABC):
    @abstractmethod
    def __init__(self, data: bitarray) -> None:
        pass

    @abstractmethod
    def decode(self) -> Schematics:
        pass
