from nand.wire import Wire, WireState


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
