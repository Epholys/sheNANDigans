import itertools
from typing import Any, Self

from nand.wire_extended_state import WireExtendedState


type WireState = WireExtendedState | bool


class Wire:
    """A Wire connecting components in a digital circuit.

    This is a "bare" wire containing only an identifier, in order to build circuits. The
    different type of wires with states used for simulation are child classes.

    This class has a static id generator: it allows to have a unique id per object. It
    is useful to quickly check the identity of wire when printing a complete circuit,
    as they are recursive.
    """

    _id_generator = itertools.count()

    def __init__(self):
        """
        Initialize a new wire with a unique ID.
        """
        self.id: int = next(Wire._id_generator)

    @property
    def state(self) -> WireState:
        raise TypeError("Trying to get the state of a bare Wire.")

    @state.setter
    def state(self, value: WireState) -> None:
        raise TypeError("Trying to set the state of a bare Wire.")

    def __str__(self) -> str:
        """Returns a placeholder as there isn't any underlying state."""
        return "X"

    def __repr__(self):
        return f"Wire(id={self.id})"

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        new_wire = type(self)()
        memo[id(self)] = new_wire
        return new_wire
