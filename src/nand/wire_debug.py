from nand.wire_extended_state import WireExtendedState
from nand.wire import Wire, WireState


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
                f"Trying to set the value of a {type(self).__name__} to an "
                f"unsupported state: {type(value).__name__}."
            )

    def __str__(self):
        """Returns the underlying state"""
        return str(self._state)

    def __repr__(self):
        """Return the full definition of the Wire, including its id."""
        return f"{type(self).__name__}(id={self.id}, state={repr(self._state)}"
