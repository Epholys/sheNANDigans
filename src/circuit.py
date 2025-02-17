from copy import deepcopy
from enum import Enum, auto
from multiprocessing import Value
from queue import SimpleQueue
from typing import Any, OrderedDict, Self, TypeAlias
import itertools
from xmlrpc.client import Boolean


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
    Represents a wire in a digital circuit that can carry binary signals.
    
    A wire connects the components in the circuits.
    It maintains a state (True/False/None) and has a unique identifier for tracking
    connections throughout the circuit.
    
    Attributes:
        state (WireState): The current state of the wire
        id (int): Unique identifier for tracking wire connections
    """
    _id_generator = itertools.count()

    def __init__(self):
        """
        Initialize a new wire with a unique ID.

        The ID is useful for having a memorable object ID to quick check
        """
        self._state : WireState = WireState.UNKNOWN
        self.id : int = next(Wire._id_generator)    


    @property
    def state(self) -> WireState:
        """Get the wire state as an enum"""
        return self._state

    @state.setter
    def state(self, value: bool | WireState) -> None:
        if isinstance(value, bool):
            self._state = WireState.ON if value else WireState.OFF
        else:
            self._state = value

    def __deepcopy__(self, memo : dict[int, Any]) -> Self:
        """
        Create a deep copy of the wire with a new unique ID.
        
        Args:
            memo (dict): Dictionary of already copied objects

        Returns:
            Wire: A new wire instance with copied state and new ID
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

CircuitId: TypeAlias = str|int

class Circuit:
    """
    Represents a digital circuit composed of components and their interconnections.

    A circuit is a collection of components (sub-circuits) connected by wires.
    It maintains its own inputs, outputs, and internal components, allowing
    for hierarchical circuit construction.
    
    Special case: When identifier=0, the circuit acts as a NAND gate,
    implementing the basic NAND logic operation.

    The attributes are ordered dictionaries, to maintain correct simulation after
    an encoding-decoding round-trip.
    
    Attributes:
        identifier (str): Unique identifier for the circuit
        inputs (OrderedDict[Any, Wire]): Input wires of the circuit
        outputs (OrderedDict[Any, Wire]): Output wires of the circuit
        components (OrderedDict[Any, Circuit]): Components of the circuit
        miss (int): Counter of the failed NAND simulation attempts

    TODO Add Example
    TODO explicit provenance model (output is clean, no propagation)
    """
        
    def __init__(self, identifier : CircuitId):
        """
        Initialize a new circuit with the given identifier.

        Args:
            identifier (str): Unique identifier for this circuit
        """
        self.identifier = identifier
        self.inputs : OrderedDict[CircuitId, Wire] = OrderedDict()
        self.outputs : OrderedDict[CircuitId, Wire] = OrderedDict()
        self.components : OrderedDict[CircuitId, Self] = OrderedDict()
        self.miss = 0

    def add_component(self, name : CircuitId, component : Self) -> None:
        self.components[name] = component

    def add_input(self, input: CircuitId, target_name: CircuitId, target_input: CircuitId) -> None:
        """
        Connect an input wire to a component's input port.
        
        Creates a new input wire if it doesn't exist and connects it to the specified
        component's input port. The connection is propagated through the circuit.
        
        Args:
            input (str): Name of the input wire to create/connect
            target_name (str): Name of the component to connect to
            target_input (str): Name of the input port on the target component
        
        Raises:
            ValueError: If target_name doesn't exist in the circuit
        """
        if target_name not in self.components:
            raise ValueError(f"Component {target_name} does not exist")
        target = self.components[target_name]

        if target_input not in target.inputs:
            raise ValueError(f"Component {target_name} does not have input wire {target_input}")
        
        if input not in self.inputs:
            self.inputs[input] = Wire()
        
        wire = self.inputs[input]    
        old_wire = target.inputs[target_input]
        target.inputs[target_input] = wire

        # Update all matching wire references in the component hierarchy
        self._propagate_wire_update(target, old_wire, wire)

        
    def add_output(self, output: CircuitId, source_name: CircuitId, source_output: CircuitId) -> None:
        """
        Connect an output wire to a component's output port.
        
        Creates a new output wire if it doesn't exist and connects it to the specified
        component's output port. The connection is propagated through the circuit.
        
        Args:
            output (str): Name of the output wire to create/connect
            source_component (str): Name of the component to connect to
            source_output (str): Name of the output port on the source component
        
        Raises:
            ValueError: If source_component doesn't exist in the circuit
        """
        if source_name not in self.components:
            raise ValueError(f"Component {source_name} does not exist")
        source = self.components[source_name]

        if source_output not in source.outputs:
            raise ValueError(f"Component {source_name} does not have output wire {source_output}")
        
        self.outputs[output] = source.outputs[source_output]

        # TODO comment why not propagation

    def add_wire(self, source_name: CircuitId, source_output: CircuitId, 
                target_name: CircuitId, target_input: CircuitId) -> None:
        """
        Connect an output port of one component to an input port of another component.
        
        Connect two components in the circuit by replacing the target component's input wire
        by the source component's output. The connection is propagated through the circuit hierarchy.
        
        Args:
            source_component (str): Name of the component providing the output
            source_output (str): Name of the output port on the source component
            target_component (str): Name of the component receiving the input
            target_input (str): Name of the input port on the target component
        
        Raises:
            ValueError: If either component doesn't exist in the circuit
            ValueError: If the specified output port doesn't exist on source component
        """        
        if source_name not in self.components:
            raise ValueError(f"Source ({source_name}) component does not exist")            
        
        if target_name not in self.components:
            raise ValueError(f"Target ({target_name}) component does not exist")            
        
        source = self.components[source_name]
        target = self.components[target_name]

        if source_output not in source.outputs:
            raise ValueError(f"Component {source_name} has no output {source_output}")
            
        if target_input not in target.inputs:
            raise ValueError(f"Component {target_name} has no input {target_input}")
        
        wire = source.outputs[source_output]
        old_wire = target.inputs[target_input]

        target.inputs[target_input] = wire
        
        self._propagate_wire_update(target, old_wire, wire)

    def _propagate_wire_update(self, component: Self, old_wire: Wire, new_wire: Wire) -> None:
        """
        Recursively update all matching wire references in a component hierarchy.

        Traverses the entire component tree to ensure consistent wire connections.
        When a wire is replaced, all references to the old wire must be updated.
        
        This is necessary because adding an input create a new Wire that
        replaces the component's input. By doing so, this component's input
        become disconnected of its own components' input. So the new Wire must replace
        recursively in all the input hierarchy.

        Args:
            component (Circuit): Starting component for the recursive update
            old_wire (Wire): Wire reference to be replaced
            new_wire (Wire): Wire reference to replace with
        """
        for subcomponents in component.components.values():
            wire_dict = subcomponents.inputs
            wire_dict.update({k: new_wire for k, w in wire_dict.items() if w.id == old_wire.id})
            self._propagate_wire_update(subcomponents, old_wire, new_wire)

    def validate(self) -> Boolean:
        # TODO : Tous les in sont câblés, tous les outs sont câblés, tous les composants sont câblés (?)
        return True

    def reset(self) -> None:
        """
        Reset the circuit to its initial state.
        
        Recursively resets:
        - All wires' state to Unknown
        - All components
        - The simulation miss counter
        """
        for wire in self.inputs.values():
            wire.state = WireState.UNKNOWN

        for wire in self.outputs.values():
            wire.state = WireState.UNKNOWN

        for component in self.components.values():
            component.reset()

        self.miss = 0

    def can_simulate(self) -> Boolean:
        return all(wire.state != WireState.UNKNOWN for wire in self.inputs.values())

    def was_simulated(self) -> Boolean:
        return all(wire.state != WireState.UNKNOWN for wire in self.outputs.values())

    def simulate(self) -> Boolean:
        """
        Simulate the circuit's behavior based on input states.
        
        Performs digital logic simulation by either:
        1. For NAND gates (identifier=0): Directly computes NAND logic
        2. For complex circuits: Iteratively simulates sub-components until either:
           - All outputs are determined (success)
           - Or no further progress can be made (deadlock)

        Returns:
            bool: True if simulation completed successfully (all outputs determined)
                 False if simulation cannot proceed or is already complete

        Note:
            Increments self.miss counter when sub-component simulation fails
        """
        if not self.can_simulate() or self.was_simulated():
            return False

        if self.identifier == 0:
            self._simulate_nand()
            return True
        
        n_evaluated = 0
        while True:
            previous_n_evaluated = n_evaluated
            for component in self.components.values():
                if component.simulate():
                    n_evaluated += 1
                else:
                    self.miss += 1

            if n_evaluated == previous_n_evaluated:
                break

        return self.was_simulated()    
    
    def _simulate_nand(self):
        inputs = list(self.inputs.values())
        a = inputs[0]
        b = inputs[1]
        out = list(self.outputs.values())[0]
        out.state = not(a.state and b.state)


    def __repr__(self, indent=0):
        indent_str = ' ' * indent
        inputs_str = ', '.join(f'{k}: {repr(v)}' for k, v in self.inputs.items())
        outputs_str = ', '.join(f'{k}: {repr(v)}' for k, v in self.outputs.items())
        components_str = ',\n'.join(f'\n{indent_str}  {k}:\n  {v.__repr__(indent + 4)}' for k, v in self.components.items())
        return (f'{indent_str}Circuit(id={self.identifier},\n'
                f'{indent_str}  inputs=OrderedDict({inputs_str}),\n'
                f'{indent_str}  outputs=OrderedDict({outputs_str}),\n'
                f'{indent_str}  components=OrderedDict({components_str})\n'
                f'{indent_str})')