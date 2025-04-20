from typing import Dict


from wire import Wire

# Type aliasing definition. There is a lot of them, but it's easier when developing to
# have clear hints.
type Key = str | int
type CircuitKey = Key
type InputKey = Key
type OutputKey = Key
type PortKey = InputKey | OutputKey
type InputWireDict = Dict[InputKey, Wire]
type OutputWireDict = Dict[OutputKey, Wire]
type PortWireDict = InputWireDict | OutputWireDict
type CircuitDict = Dict[CircuitKey, "Circuit"]


class Circuit:
    """A digital circuit recursively composed of other circuits
    and their interconnections.

    A circuit is a collection of inputs, outputs, and components connected by wires.
    As components are circuit themselves, it's internal representation is close to
    a tree.

    The attributes are dictionaries, and depends on them being ordered. Which they are
    since Python 3.7

    This class is used as the data structure for all other parts of this project,
    and as a builder of these data.

    This data structure is independent of simulations and encoding. However, the NAND
    logic gate is implicitly used in all of these applications. As such, the int
    identifier '0' is reserved for it, and it's also expected that the leaves of
    the tree-like components structure are composed exclusively of these gates.

    Attributes:
        identifier: Identifier of the circuit. Uniqueness is necessary if
        several circuits are bundled into a Schematics library. 0 is reserved for
        the base NAND circuit.

        inputs: Input wires of the circuit
        outputs: Output wires of the circuit
        components: Components of the circuit
    """

    def __init__(self, identifier: CircuitKey):
        self.identifier = identifier
        self.inputs: InputWireDict = {}
        self.outputs: OutputWireDict = {}
        self.components: CircuitDict = {}

    def add_component(self, id: CircuitKey, component: "Circuit"):
        """Add a component.

        Args:
            id: Identifier of the component.
            component: The component itself.
        """
        self.components[id] = component

    def connect_input(
        self, input: InputKey, target_id: CircuitKey, target_input: InputKey
    ):
        """Connect an input wire to a component's input port.

        Creates a new input wire if it doesn't exist and connects it to the specified
        component's input port. The connection is propagated through the circuit.

        Args:
            input: Identifier of the input wire to create/connect
            target_name: Identifier of the component to connect to
            target_input: Identifier of the input port on the target component

        Raises:
            ValueError: If the target or its input doesn't exists
        """
        if target_id not in self.components:
            raise ValueError(f"The component {target_id} does not exist.")
        target = self.components[target_id]

        if target_input not in target.inputs:
            raise ValueError(
                f"The component {target_id} does not have input wire {target_input}."
            )

        if input not in self.inputs:
            self.inputs[input] = Wire()

        # The assignment ordering dance is necessary. Setting 'input' as the
        # 'target_input' doesn't work, there is an edge case.
        # A single input can be connected to several component's input(s).
        # So, it's the components' target inputs that must be set and propagated.
        wire = self.inputs[input]
        old_wire = target.inputs[target_input]
        target.inputs[target_input] = wire

        # Update all matching wire references in the component hierarchy.
        self._propagate_wire_update(target, old_wire, wire)

    def connect_output(
        self, output: OutputKey, source_name: CircuitKey, source_output: OutputKey
    ):
        """Connect an output wire to a component's output port.

        Creates a new output wire if it doesn't exist and connects it to the specified
        component's output port.

        Args:
            output: Identifier of the output wire to create/connect.
            source_name: Identifier of the component to connect to
            source_output: Identifier of the output port on the source component

        Raises:
            ValueError: If the source or its output doesn't exist
        """
        if source_name not in self.components:
            raise ValueError(f"The component {source_name} does not exist.")
        source = self.components[source_name]

        if source_output not in source.outputs:
            raise ValueError(
                f"The component {source_name} does not have "
                f"output wire {source_output}."
            )

        # Contrary to the connection of an input, connecting an output is
        # straightforward: the circuit's output can only come from a single component.
        self.outputs[output] = source.outputs[source_output]

    def connect(
        self,
        source_id: CircuitKey,
        source_output: OutputKey,
        target_id: CircuitKey,
        target_input: InputKey,
    ):
        """Connect an output port of one component to an input port of another component

        Connect two components in the circuit by replacing the target component's input
        wire by the source component's output. The connection is propagated through the
        circuit hierarchy.

        Args:
            source_id: Identifier of the component providing the output.
            source_output: Identifier of the output port on the source component.
            target_id: Identifier of the component receiving the input.
            target_input: Identifier of the input port on the target component.

        Raises:
            ValueError: If either component doesn't exist in the circuit or if the
            specified ports doesn't exist on source or target components.
        """
        if source_id not in self.components:
            raise ValueError(f"The source component {source_id} does not exist.")

        if target_id not in self.components:
            raise ValueError(f"The target component {target_id} does not exist.")

        source = self.components[source_id]
        target = self.components[target_id]

        if source_output not in source.outputs:
            raise ValueError(
                f"The source component {source_id}"
                f"does not have output wire {source_output}."
            )

        if target_input not in target.inputs:
            raise ValueError(
                f"The source component {target_id}"
                f"does not have input wire {target_input}."
            )

        # Same logic as the connect_input() method.
        wire = source.outputs[source_output]
        old_wire = target.inputs[target_input]
        target.inputs[target_input] = wire

        # Update all matching wire references in the component hierarchy.
        self._propagate_wire_update(target, old_wire, wire)

    def _propagate_wire_update(
        self, component: "Circuit", old_wire: Wire, new_wire: Wire
    ):
        """Recursively update all matching wire references in a component hierarchy.

        Traverses the entire component tree to ensure consistent wire connections.
        When a wire is replaced, all references to the old wire must be updated.

        Args:
            component: The starting component from which the wires must be recursively
            updated.

            old_wire: Wire to replace.
            new_wire: Wire to replace with.
        """
        for sub_components in component.components.values():
            wire_dict = sub_components.inputs
            updates = {k: new_wire for k, w in wire_dict.items() if w.id == old_wire.id}
            if len(updates) != 0:
                wire_dict.update(updates)
                self._propagate_wire_update(sub_components, old_wire, new_wire)

    def __str__(self, indent: int = 0):
        """Human-readable string representation of the Circuit with clear indentation.
        Shows basic information about the circuit structure in a compact format.

        The goal is to represent the structure itself: so the type or state of the wires
        are not included, only their identifier.
        """
        indent_str = " " * indent

        # Format input wires
        inputs_str = ", ".join(f"{k}: {v.id}" for k, v in self.inputs.items())

        # Format output wires
        outputs_str = ", ".join(f"{k}: : {v.id}" for k, v in self.outputs.items())

        representation = (
            f"({self.identifier}, inputs={{{inputs_str}}}, outputs={{{outputs_str}}}"
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

        return representation

    def __repr__(self, indent: int = 4):
        """Complete debug string of the Circuit, with clear indentation."""
        indent_str = " " * indent

        # Format input wires
        inputs_str = ", ".join(f"{k}: {repr(v)}" for k, v in self.inputs.items())

        # Format output wires
        outputs_str = ", ".join(f"{k}: {repr(v)}" for k, v in self.outputs.items())

        representation = (
            f"Circuit(identifier={self.identifier}"
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

        return representation
