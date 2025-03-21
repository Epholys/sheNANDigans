from enum import Enum, auto
import itertools
from typing import Any, Self


class WireExtendedState(Enum):
    """The possible states of a Wire.

    This is an "extended state", as it allows an Unknown state to represent
    uninitialized or not yet computed values.
    """

    UNKNOWN = auto()
    OFF = auto()
    ON = auto()

    def __bool__(self) -> bool:
        match self:
            case WireExtendedState.OFF:
                return False
            case WireExtendedState.ON:
                return True
            case WireExtendedState.UNKNOWN:
                raise TypeError("Trying to cast the UNKNOWN state to a boolean.")

    def __int__(self) -> int:
        match self:
            case WireExtendedState.OFF:
                return 0
            case WireExtendedState.ON:
                return 1
            case WireExtendedState.UNKNOWN:
                raise TypeError("Trying to convert the UNKONWN state to an integer.")

    def __str__(self):
        match self:
            case WireExtendedState.OFF:
                return "0"
            case WireExtendedState.ON:
                return "1"
            case WireExtendedState.UNKNOWN:
                return "?"


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


class WireDebug(Wire):
    """A Wire in a digital circuit used for debugging.

    Its internal state can not only be ON or OFF, but also UNKNOWN.
    It's useful for debugging, as the unknown state during simulation indicates an error
    in the circuit definition, or in the simulation itself.
    """

    def __init__(self):
        super().__init__()
        self._state: WireExtendedState = WireExtendedState.UNKNOWN

    @property
    def state(self) -> WireExtendedState:
        return self._state

    @state.setter
    def state(self, value: WireState):
        if isinstance(value, WireExtendedState):
            self._state = value
        elif isinstance(value, bool):
            self._state = WireExtendedState.ON if value else WireExtendedState.OFF
        else:
            raise TypeError(
                f"Trying to set the value of a {type(self).__name__} to an"
                f"unsupported state: {type(value).__name__}."
            )

    def __str__(self):
        """Returns the underlying state"""
        return str(self._state)

    def __repr__(self):
        """Return the full definition of the Wire, including its id."""
        return f"{type(self).__name__}(id={self.id}, state={repr(self._state)}"


class WireFast(Wire):
    """A Wire in a digital circuit that carries binary signals.

    This is a "classic" wire, containing a boolean for its state. As such, it's faster
    than having a more complex state, but there isn't any security if a definition or a
    simulation is wrong.
    """

    def __init__(self):
        super().__init__()
        self._state: bool = False

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, value: WireState):
        if isinstance(value, bool):
            self._state = value
        else:
            raise ValueError(
                f"Trying to set the value of the {type(self).__name__}'s boolean state"
                f"to a more complex WireState ({type(value).__name__})."
            )

    def __str__(self):
        """Returns the underlying state"""
        return "1" if self._state else "0"

    def __repr__(self):
        return f"WireFast(id={self.id}, state={self._state})"
