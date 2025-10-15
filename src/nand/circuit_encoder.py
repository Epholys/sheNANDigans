from abc import ABC, abstractmethod
from bitarray import bitarray

from nand.circuit_builder import CircuitLibrary

type BitArrayLike = bitarray | list[int]
class CircuitEncoder(ABC):
    # TODO for both encoders/decoders: make it stateless (reusing one breaks everything)
    @abstractmethod
    def encode(self, library: CircuitLibrary) -> BitArrayLike:
        pass
