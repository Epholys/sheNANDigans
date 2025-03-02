from typing import Dict, TypeAlias

from wire import Wire, WireState

CircuitKey: TypeAlias = str | int
WireDict: TypeAlias = Dict[CircuitKey, Wire]
CircuitDict: TypeAlias = Dict[CircuitKey, "Circuit"]


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

    Attributes: # TODO change : auto change ?
        identifier (str): Unique identifier for the circuit
        inputs (OrderedDict[Any, Wire]): Input wires of the circuit
        outputs (OrderedDict[Any, Wire]): Output wires of the circuit
        components (OrderedDict[Any, Circuit]): Components of the circuit
        miss (int): Counter of the failed NAND simulation attempts

    TODO Add Example
    TODO Explain provenance model
    """

    def __init__(self, identifier: CircuitKey):
        """
        Initialize a new circuit with the given identifier.
        """
        self.identifier = identifier
        self.inputs: WireDict = dict()
        self.outputs: WireDict = dict()
        self.components: CircuitDict = dict()
        self.miss = 0

    def add_component(self, name: CircuitKey, component: "Circuit"):
        self.components[name] = component

    def connect_input(
        self, input: CircuitKey, target_name: CircuitKey, target_input: CircuitKey
    ):
        """
        Connect an input wire to a component's input port.

        Creates a new input wire if it doesn't exist and connects it to the specified
        component's input port. The connection is propagated through the circuit.

        Args:
            input: ID of the input wire to create/connect
            target_name: ID of the component to connect to
            target_input: ID of the input port on the target component

        Raises:
            ValueError: If the target or its input doesn't exists
        """
        if target_name not in self.components:
            raise ValueError(f"Component {target_name} does not exist")
        target = self.components[target_name]

        if target_input not in target.inputs:
            raise ValueError(
                f"Component {target_name} does not have input wire {target_input}"
            )

        if input not in self.inputs:
            self.inputs[input] = Wire()

        # Setting 'input' as the 'target_input' doesn't work, there a edge cases.
        # A single input can be connected to several component's input(s).
        # So, it's the components' target inputs that must be set and propagated.
        wire = self.inputs[input]
        old_wire = target.inputs[target_input]
        target.inputs[target_input] = wire

        # Update all matching wire references in the component hierarchy
        self._propagate_wire_update(target, old_wire, wire)

    def connect_output(
        self, output: CircuitKey, source_name: CircuitKey, source_output: CircuitKey
    ):
        """
        Connect an output wire to a component's output port.

        Creates a new output wire if it doesn't exist and connects it to the specified
        component's output port. The connection is propagated through the circuit.

        Args:
            output: ID of the output wire to create/connect
            source_component: ID of the component to connect to
            source_output: ID Name of the output port on the source component

        Raises:
            ValueError: If the source or its output doesn't exist
        """
        if source_name not in self.components:
            raise ValueError(f"Component {source_name} does not exist")
        source = self.components[source_name]

        if source_output not in source.outputs:
            raise ValueError(
                f"Component {source_name} does not have output wire {source_output}"
            )

        # Contrary to connecting an input, connecting a output is straightforward: the circuit's
        # output can only come from a single component.
        self.outputs[output] = source.outputs[source_output]

    def connect(
        self,
        source_name: CircuitKey,
        source_output: CircuitKey,
        target_name: CircuitKey,
        target_input: CircuitKey,
    ):
        """
        Connect an output port of one component to an input port of another component.

        Connect two components in the circuit by replacing the target component's input wire
        by the source component's output. The connection is propagated through the circuit hierarchy.

        Args:
            source_component: ID of the component providing the output
            source_output: ID of the output port on the source component
            target_component: ID of the component receiving the input
            target_input: ID of the input port on the target component

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

    def _propagate_wire_update(
        self, component: "Circuit", old_wire: Wire, new_wire: Wire
    ):
        """
        Recursively update all matching wire references in a component hierarchy.

        Traverses the entire component tree to ensure consistent wire connections.
        When a wire is replaced, all references to the old wire must be updated.

        This is necessary because updating the input of a component does not update
        the linked inputs of its own components.

        Args:
            component: Starting component for the recursive update
            old_wire: Wire to replace
            new_wire: Wire to replace with
        """
        for subcomponents in component.components.values():
            wire_dict = subcomponents.inputs
            wire_dict.update(
                {k: new_wire for k, w in wire_dict.items() if w.id == old_wire.id}
            )
            self._propagate_wire_update(subcomponents, old_wire, new_wire)

    def validate(self) -> bool:
        # TODO
        # Tous les in sont câblés, tous les outs sont câblés, tous les composants sont câblés (?),
        # outs <-!-> ins
        # no cycles
        # https://en.wikipedia.org/wiki/Topological_sorting https://docs.python.org/3/library/graphlib.html
        # https://networkx.org/documentation/stable/
        # https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.is_directed_acyclic_graph.html#networkx.algorithms.dag.is_directed_acyclic_graph
        # https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.components.is_weakly_connected.html
        # no dangling wires
        # no unused components
        # all ins and all outs used
        # ins > 0, outs > 0, composants > 0
        return True

    def reset(self):
        """
        Reset the circuit to its initial state.

        Resets:
        - All wires' state to Unknown
        - All components recursively
        - The simulation miss counter
        """
        for wire in self.inputs.values():
            wire.state = WireState.UNKNOWN

        for wire in self.outputs.values():
            wire.state = WireState.UNKNOWN

        for component in self.components.values():
            component.reset()

        self.miss = 0

    def can_simulate(self) -> bool:
        """Check if the circuit can be simulated, meaning that all inputs are determined."""
        return all(wire.state != WireState.UNKNOWN for wire in self.inputs.values())

    def was_simulated(self) -> bool:
        """Check if the circuit was simulated, meaning that all outputs are determined."""
        return all(wire.state != WireState.UNKNOWN for wire in self.outputs.values())

    def simulate(self) -> bool:
        """
        Simulate the circuit's behavior.

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

        # There are much more "elegant" ways to do it (using any for example), but my brain
        # isn't python-wired enough to be sure to understand it tomorrow.
        while True:
            progress_made = False
            for component in self.components.values():
                if component.simulate():
                    progress_made = True
                else:
                    self.miss += 1

            if not progress_made:
                break

        return self.was_simulated()

    def _simulate_nand(self):
        """Simulate a NAND gate"""
        inputs = list(self.inputs.values())
        a = inputs[0]
        b = inputs[1]
        out = list(self.outputs.values())[0]
        out.state = not (a.state and b.state)

    def __str__(self, indent: int = 0):
        """
        Human-readable string representation of the Circuit with clear indentation.
        Shows basic information about the circuit structure in a compact format.
        """
        indent_str = " " * indent

        # Format input wires
        inputs_str = ", ".join(f"{k}: W({v.id})" for k, v in self.inputs.items())

        # Format output wires
        outputs_str = ", ".join(f"{k}: W({v.id})" for k, v in self.outputs.items())

        representation = (
            f"C(id={self.identifier}, inputs=({inputs_str}), outputs=({outputs_str})"
        )

        # Format components (only for non-NAND gates)
        if self.identifier != 0:
            components_list = [
                f"{k}: {v.__str__(indent + 4)}" for k, v in self.components.items()
            ]
            components_str = (
                "{\n"
                + indent_str
                + "  "
                + f",\n{indent_str}  ".join(components_list)
                + "\n"
                + indent_str
                + "}"
            )
            representation += f", components={components_str}"

        representation += ")"

        # Build the final representation
        return representation

    def __repr__(self, indent: int = 4):
        """Complete debug string of the Circuit, trying to make it legible with indentation"""
        indent_str = " " * indent

        # Format input wires
        inputs_str = ", ".join(f"{k}: Wire(id={v.id})" for k, v in self.inputs.items())

        # Format output wires
        outputs_str = ", ".join(
            f"{k}: Wire(id={v.id})" for k, v in self.outputs.items()
        )

        representation = (
            f"Circuit(id={self.identifier}"
            f", inputs=({inputs_str})"
            f", outputs=({outputs_str})"
        )

        # Format components (only for non-NAND gates)
        if self.identifier != 0:
            components_list = [
                f"{k}: {v.__repr__(indent + 4)}" for k, v in self.components.items()
            ]
            components_str = (
                "{\n"
                + indent_str
                + "  "
                + f",\n{indent_str}  ".join(components_list)
                + "\n"
                + indent_str
                + "}"
            )
            representation += f", components={components_str}"

        representation += ")"

        # Build the final representation
        return representation
