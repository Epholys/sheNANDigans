

from enum import Enum, auto
import itertools
from typing import Any, Self


class WireState(Enum):
    UNKNOWN = auto()
    OFF =  auto()
    ON =  auto()

    def __bool__(self) -> bool:
        match self:
            case WireState.OFF:
                return False
            case WireState.ON:
                return True
            case WireState.UNKNOWN:
                raise ValueError(f"Trying to convert an Unknown state to a boolean.")
            
    def __int__(self) -> int:
        match self:
            case WireState.OFF:
                return 0
            case WireState.ON:
                return 1
            case WireState.UNKNOWN:
                raise ValueError(f"Trying to convert an Unknown state to a boolean.")
    
class Wire:
    """
    Represents a wire in a digital circuit that carry binary signals.
    
    A wire connects the components in the circuits.
    It maintains a state (On/Off/Unknown) and has a unique identifier for tracking
    connections throughout the circuit.
    
    Attributes:
        state (WireState): The current state of the wire
        id (int): Unique identifier for tracking connections
    """
    _id_generator = itertools.count()

    def __init__(self):
        """
        Initialize a new wire with a unique ID.

        The ID allow to quick check while debugging
        """
        self._state : WireState = WireState.UNKNOWN
        self.id : int = next(Wire._id_generator)    


    @property
    def state(self) -> WireState:
        return self._state

    @state.setter
    def state(self, value: bool | WireState) :
        if isinstance(value, bool):
            self._state = WireState.ON if value else WireState.OFF
        else:
            self._state = value

    def __deepcopy__(self, memo : dict[int, Any]) -> Self:
        """
        Create a deep copy of the wire with a new unique ID.
        """
        new_wire = type(self)()
        memo[id(self)] = new_wire
        return new_wire

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
            case WireState.OFF:
                return "0"
            case WireState.ON:
                return "1" 
            case WireState.UNKNOWN:
                return "X"