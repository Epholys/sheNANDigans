import copy

from itertools import groupby
from typing import Dict, List, Tuple

import networkx

from simulator_builder import OptimizationLevel, build_simulator, get_wire_class
from simulator import Simulator
from wire import Wire


type Key = str | int
type CircuitKey = Key
type InputKey = Key
type OutputKey = Key
type InputWireDict = Dict[InputKey, Wire]
type OutputWireDict = Dict[OutputKey, Wire]
type PortWireDict = InputWireDict | OutputWireDict
type CircuitDict = Dict[CircuitKey, "Circuit"]


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

    def __init__(
        self,
        identifier: CircuitKey,
        optimization_level: OptimizationLevel = OptimizationLevel.FAST,
    ):
        """
        Initialize a new circuit with the given identifier.
        """
        self.identifier = identifier
        self.inputs: InputWireDict = dict()
        self.outputs: OutputWireDict = dict()
        self.components: CircuitDict = dict()
        self.components_stack: List[Circuit] = []
        self.graph = networkx.DiGraph()
        self._optimization_level = optimization_level
        self._wire_class = get_wire_class(optimization_level)
        self._simulator: Simulator = build_simulator(self, optimization_level)

    def add_component(self, name: CircuitKey, component: "Circuit"):
        self.components[name] = component

    def connect_input(
        self, input: InputKey, target_name: CircuitKey, target_input: InputKey
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
            self.inputs[input] = self._wire_class()

        # Setting 'input' as the 'target_input' doesn't work, there a edge cases.
        # A single input can be connected to several component's input(s).
        # So, it's the components' target inputs that must be set and propagated.
        wire = self.inputs[input]
        old_wire = target.inputs[target_input]
        target.inputs[target_input] = wire

        # Update all matching wire references in the component hierarchy
        self._propagate_wire_update(target, old_wire, wire)

    def connect_output(
        self, output: OutputKey, source_name: CircuitKey, source_output: OutputKey
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
        source_output: OutputKey,
        target_name: CircuitKey,
        target_input: InputKey,
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
            raise ValueError(
                f"Source component ({source_name}) component does not exist"
            )

        if target_name not in self.components:
            raise ValueError(
                f"Target component ({target_name}) component does not exist"
            )

        source = self.components[source_name]
        target = self.components[target_name]

        if source_output not in source.outputs:
            raise ValueError(
                f"Source component {source_name} has no output {source_output}"
            )

        if target_input not in target.inputs:
            raise ValueError(
                f"Source component {target_name} has no input {target_input}"
            )

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

    def concludes(self, recursive: bool):
        # self.optimize(recursive)
        self.validate()

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

    def optimize(self, recursive: bool):
        if len(self.components) == 0:
            return

        if recursive:
            for component in self.components.values():
                component.optimize(recursive)

        components: List[Circuit] = [
            component for component in self.components.values()
        ]

        raw_components_inputs: List[Tuple[str, List[Wire]]] = [
            (f"comp_in_{component.identifier}_{idx}", list(component.inputs.values()))
            for idx, component in enumerate(components)
        ]

        components_inputs: List[Tuple[str, Wire]] = [
            (key, wire) for key, wires in raw_components_inputs for wire in wires
        ]

        raw_components_outputs: List[Tuple[str, List[Wire]]] = [
            (f"comp_out_{component.identifier}_{idx}", list(component.outputs.values()))
            for idx, component in enumerate(components)
        ]

        components_outputs: List[Tuple[str, Wire]] = [
            (key, wire) for key, wires in raw_components_outputs for wire in wires
        ]

        inputs: List[Tuple[str, Wire]] = list(
            (f"ct_in_{input[0]}_{idx}", input[1])
            for idx, input in enumerate(self.inputs.items())
        )
        outputs: List[Tuple[str, Wire]] = list(
            (f"ct_out_{output[0]}_{idx}", output[1])
            for idx, output in enumerate(self.outputs.items())
        )

        for input in inputs:
            for component_input in components_inputs:
                if input[1].id == component_input[1].id:
                    self.graph.add_edge(input[0], component_input[0])

        for output in outputs:
            for component_output in components_outputs:
                if output[1].id == component_output[1].id:
                    self.graph.add_edge(component_output[0], output[0])

        for component_output in components_outputs:
            for component_input in components_inputs:
                if component_input[1] == component_output[1]:
                    self.graph.add_edge(component_output[0], component_input[0])

        sorted = list(networkx.topological_sort(self.graph))
        components_named_duplicate = [key for key, _ in components_inputs]
        components_named = [key for key, _ in groupby(components_named_duplicate)]
        sorted_only_components = [
            comp_name for comp_name in sorted if comp_name in components_named_duplicate
        ]

        indices_order: List[int] = []
        for node in sorted_only_components:
            indices_order.append(components_named.index(node))
        components_list: List[Tuple[CircuitKey, "Circuit"]] = list(
            self.components.items()
        )
        ordered_components: CircuitDict = {}
        for index in indices_order:
            (key, component) = components_list[index]
            ordered_components[key] = component
        self.components = ordered_components

    def set_optimization(self, level: OptimizationLevel):
        from circuit_converter import convert_wires

        if self._optimization_level == level:
            pass

        self._optimization_level = level
        self._wire_class = get_wire_class(level)
        convert_wires(self, self._wire_class)
        self._simulator = build_simulator(self, level)

    def reset(self):
        self._simulator.reset(self)

    def simulate(self) -> bool:
        simulation = self._simulator.simulate(self)
        return simulation

    def simulate_queue(self) -> bool:
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
        if self.identifier == 0:
            # self._simulate_nand()
            return True

        # There are much more "elegant" ways to do it (using any for example), but my brain
        # isn't python-wired enough to be sure to understand it tomorrow.
        while True:
            to_simulate = len(self.components_stack)
            for _ in range(to_simulate):
                component = self.components_stack.pop(0)
                if not component.simulate_queue():
                    self.components_stack.append(component)
            left = len(self.components_stack)

            if to_simulate == left:
                break

        return True

    def __deepcopy__(self, memo):
        """Create a deep copy of the wire with a new unique ID.

        Technically, this method isn't necessary: the default Python's deepcopy method is enough.
        I still prefer to define it: Wire must define this method, so this is a way to
        have an explicit control flow.

        Args:
            memo (Any): The memory of already copied objects.

        Returns:
            Self: A new deepcopy object.
        """
        new_circuit = type(self)(self.identifier, self._optimization_level)
        memo[id(self)] = new_circuit

        new_circuit.inputs = {
            key: copy.deepcopy(wire, memo) for key, wire in self.inputs.items()
        }
        new_circuit.outputs = {
            key: copy.deepcopy(wire, memo) for key, wire in self.outputs.items()
        }
        new_circuit.components = {
            key: copy.deepcopy(wire, memo) for key, wire in self.components.items()
        }

        return new_circuit

    def __str__(self, indent: int = 0):
        """
        Human-readable string representation of the Circuit with clear indentation.
        Shows basic information about the circuit structure in a compact format.
        """
        indent_str = " " * indent

        # Format input wires
        inputs_str = ", ".join(f"{k}: W({v.id}, {v})" for k, v in self.inputs.items())

        # Format output wires
        outputs_str = ", ".join(f"{k}: W({v.id}, {v})" for k, v in self.outputs.items())

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
        inputs_str = ", ".join(f"{k}: {repr(v)}" for k, v in self.inputs.items())

        # Format output wires
        outputs_str = ", ".join(f"{k}: {repr(v)}" for k, v in self.outputs.items())

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
