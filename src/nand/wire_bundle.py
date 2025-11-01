import itertools
from copy import deepcopy
from typing import Any, Self

from nand.wire import Wire


class WireBundle:
    _id_generator = itertools.count()

    def __init__(self, size: int = 1):
        self.id: int = next(WireBundle._id_generator)
        self.size = size
        self.wires: list[Wire] = [Wire() for _ in range(size)]

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        new_bundle = type(self)()
        memo[id(self)] = new_bundle
        self.wires = [deepcopy(wire) for wire in self.wires]
        return new_bundle

    # TODO : __str__() for bundle

class SingleWire(WireBundle):
    def __init__(self):
        super().__init__()
        self.wire = self.wires[0]