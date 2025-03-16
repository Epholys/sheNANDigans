from abc import ABC, abstractmethod
from enum import Enum, auto
import itertools
from typing import Any, Self


class WireExtendedState(Enum):
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
                raise ValueError(
                    "Something went wrong: trying to cast the UNKNOWN state to a boolean"
                )

    def __int__(self) -> int:
        match self:
            case WireExtendedState.OFF:
                return 0
            case WireExtendedState.ON:
                return 1
            case WireExtendedState.UNKNOWN:
                raise ValueError(
                    "Something went wrong: : trying to convert the UNKONWN state to an integer."
                )


type WireState = WireExtendedState | bool


class Wire(ABC):
    _id_generator = itertools.count()

    def __init__(self):
        """
        Initialize a new wire with a unique ID.

        The ID allow to quick check while debugging
        """
        self.id: int = next(Wire._id_generator)

    @property
    @abstractmethod
    def state(self) -> WireState:
        pass

    @state.setter
    @abstractmethod
    def state(self, value: WireState):
        pass

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        """
        Create a deep copy of the wire with a new unique ID.

        Args:
            memo (Any): The memory of already copied objects.

        Returns:
            Self: A new deepcopy object.
        """
        # Automatically creates a new id.
        new_wire = type(self)()
        memo[id(self)] = new_wire
        return new_wire


class WireDebug(Wire):
    """
    Represents a wire in a digital circuit that carry binary signals.

    A wire connects the components in the circuits.
    It maintains a state (On/Off/Unknown) and has a unique identifier for tracking
    connections throughout the circuit.

    Attributes:
        state (WireState): The current state of the wire
        id (int): Unique identifier for tracking connections
    """

    def __init__(self):
        """
        Initialize a new wire with a unique ID.

        The ID allow to quick check while debugging
        """
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
            raise ValueError(
                f"Trying to set the value of a {type(self).__name__} to an unsupported WireState {type(value).__name__}."
            )

    def __repr__(self):
        """
        Return detailed string representation of the wire.

        Useful for debugging purpose, to easily track its ID through a circuit.
        """
        return f"Wire(id={self.id}, state={self._state})"

    def __str__(self):
        """
        Return simple string representation of wire state (0/1/X).

        Useful to check the simulations results.
        """
        match self._state:
            case WireExtendedState.OFF:
                return "0"
            case WireExtendedState.ON:
                return "1"
            case WireExtendedState.UNKNOWN:
                return "?"


class WireFast(Wire):
    """
    Represents a wire in a digital circuit that carry binary signals.

    A wire connects the components in the circuits.
    It maintains a state (On/Off/Unknown) and has a unique identifier for tracking
    connections throughout the circuit.

    Attributes:
        state (WireState): The current state of the wire
        id (int): Unique identifier for tracking connections
    """

    def __init__(self):
        """
        Initialize a new wire with a unique ID.

        The ID allow to quick check while debugging
        """
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
                f"Trying to set the value of the {type(self).__name__}'s boolean state to a more complex WireState ({type(value).__name__})."
            )

    def __repr__(self):
        """
        Return detailed string representation of the wire.

        Useful for debugging purpose, to easily track its ID through a circuit.
        """
        return f"Wire(id={self.id}, state={self._state})"

    def __str__(self):
        """
        Return simple string representation of wire state (0/1/X).

        Useful to check the simulations results.
        """
        return "1" if self._state else "0"
