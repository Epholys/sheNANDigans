from enum import Enum, auto


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
                raise TypeError("Trying to convert the UNKNOWN state to an integer.")

    def __str__(self):
        match self:
            case WireExtendedState.OFF:
                return "0"
            case WireExtendedState.ON:
                return "1"
            case WireExtendedState.UNKNOWN:
                return "?"
