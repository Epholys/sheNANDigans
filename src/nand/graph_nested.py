import pydot
from typing import Dict, Optional, Tuple
from nand.bit_packed_decoder import BitPackedDecoder
from nand.bit_packed_encoder import BitPackedEncoder
from nand.circuit import (
    Circuit,
    CircuitId,
    InputId,
    PortId,
    PortNameDict,
    PortWireDict,
)
from nand.default_decoder import DefaultDecoder
from nand.schematics import SchematicsBuilder
from nand.graph_node_builder import NodeBuilder
from nand.default_encoder import DefaultEncoder


class GraphOptions:
    """Options for generating the circuit graph."""

    def __init__(
        self, is_compact: bool, is_aligned: bool, bold_io: bool, max_depth: int = -1
    ):
        # 'compact' means that the NAND gates are not expanded,
        # but just represented as a box.
        self.is_compact = is_compact

        # 'aligned' means that the inputs and outputs ports of the circuit are aligned
        # in a single vertical line.
        self.is_aligned = is_aligned

        # 'bold_io' means that the inputs and outputs wires of the circuit are bolded.
        self.bold_io = bold_io

        # 'max_depth' means that the circuit is expanded only to a certain depth.
        self.max_depth = max_depth


# A mapping between a circuit's ports and its graph node ID + name
type PortNodeDict = Dict[PortId, Tuple[str, str]]
# A mapping between circuit components and their ports
type ComponentsPortsDict = Dict[CircuitId, PortNodeDict]


class CircuitBuildContext:
    """Context for building a circuit graph.

    It's used to allow recursive building of nested components: a context is created
    for each component, with its own graph and prefix. So, each component can be built
    independently, and then added to the parent graph.
    """

    def __init__(
        self,
        circuit: Circuit,
        graph: pydot.Graph,
        prefix: str,
        depth: int,
        parent_context: Optional["CircuitBuildContext"] = None,
    ):
        self.circuit = circuit
        self.graph = graph
        self.prefix = prefix
        self.depth = depth
        self.parent_context = parent_context
        self.port_nodes: PortNodeDict = {}
        self.components_ports: ComponentsPortsDict = {}

    def create_component_context(
        self, component: Circuit, component_id: CircuitId
    ) -> "CircuitBuildContext":
        """Create a new context for a component."""
        # Unique prefix for the component
        # This prefix is used to create unique node IDs for the component's ports
        component_prefix = f"{self.prefix}_comp_{component_id}"

        # Build a new subgraph for the component
        graph = pydot.Cluster(
            f"cluster_{component_prefix}",
            label=f"Circuit {component.name}",
            style="rounded,filled",
            fillcolor="#f0f0f0",
            color="#000000",
        )

        return CircuitBuildContext(
            circuit=component,
            graph=graph,
            prefix=component_prefix,
            depth=self.depth + 1,
            parent_context=self,
        )

    def add_component_ports(self, component_id: CircuitId, ports: PortNodeDict) -> None:
        """Add all ports for a component."""
        self.components_ports[component_id] = ports

    def is_main_graph(self) -> bool:
        """Check if this is the main graph context."""
        return self.parent_context is None

    def add_subgraph_to_parent(self) -> None:
        """Add this context's graph to its parent graph."""
        if self.parent_context and self.graph != self.parent_context.graph:
            self.parent_context.graph.add_subgraph(self.graph)


class NestedGraphBuilder:
    """Main class for building circuit graphs."""

    def __init__(self, options: GraphOptions):
        self.options = options
        self.node_builder = NodeBuilder()

    def build_graph(self, circuit: Circuit) -> pydot.Dot:
        """Build a graph representation of the circuit."""
        # Create the main graph
        graph = pydot.Dot(
            f"Circuit_{circuit.identifier}",
            graph_type="digraph",
            rankdir="LR",
            label=circuit.identifier,
        )

        # Create the root context
        context = CircuitBuildContext(
            circuit=circuit, graph=graph, prefix="", depth=0, parent_context=None
        )

        # Build the circuit graph
        self._build_circuit_graph(context)

        return graph

    def _build_circuit_graph(self, context: CircuitBuildContext) -> None:
        """Recursively build a circuit and its components as nested subgraphs."""
        # Add port nodes
        self._add_circuit_ports(context)

        # Build components
        self._build_components(context)

        # Connect all the parts
        self._connect_all_parts(context)

        # Add the subgraph to the parent graph if needed
        context.add_subgraph_to_parent()

    def _add_circuit_ports(self, context: CircuitBuildContext) -> None:
        """Add input and output port nodes to the graph."""
        if self.options.is_aligned:
            self._add_aligned_ports(
                context,
                context.circuit.inputs,
                context.circuit.inputs_names,
                f"{context.prefix}_in",
                "#aaffaa",
                "min",
            )
            self._add_aligned_ports(
                context,
                context.circuit.outputs,
                context.circuit.outputs_names,
                f"{context.prefix}_out",
                "#ffaaaa",
                "max",
            )
        else:
            self._add_ports(
                context,
                context.circuit.inputs,
                context.circuit.inputs_names,
                f"{context.prefix}_in",
                "#aaffaa",
            )
            self._add_ports(
                context,
                context.circuit.outputs,
                context.circuit.outputs_names,
                f"{context.prefix}_out",
                "#ffaaaa",
            )

    def _add_ports(
        self,
        context: CircuitBuildContext,
        ports: PortWireDict,
        ports_names: PortNameDict,
        prefix: str,
        color: str,
    ) -> PortNodeDict:
        """Add port nodes to the graph."""
        port_nodes: PortNodeDict = {}
        for port_id in ports.keys():
            node_id = self.node_builder.create_port_node(
                context.graph,
                port_id,
                prefix,
                color,
                port_name=ports_names[port_id],
            )
            port_nodes[port_id] = node_id, ports_names[port_id]
        context.port_nodes.update(port_nodes)
        return port_nodes

    def _add_aligned_ports(
        self,
        context: CircuitBuildContext,
        ports: PortWireDict,
        ports_names: PortNameDict,
        prefix: str,
        color: str,
        rank: str,
    ) -> None:
        """Add port nodes to the graph with rank alignment."""
        circuit_ports = self._add_ports(context, ports, ports_names, prefix, color)

        # Create a subgraph to align the ports
        subgraph_name = f"{prefix}_aligned_{rank}"
        subgraph = pydot.Subgraph(subgraph_name, rank=rank)

        for node_id, node_name in circuit_ports.values():
            subgraph.add_node(pydot.Node(node_id, label=node_name))

        context.graph.add_subgraph(subgraph)

    def _build_components(self, context: CircuitBuildContext) -> None:
        """Build all components in the circuit."""
        components = context.circuit.components

        # Case 1: We're at a NAND gate leaf node and not using compact representation
        if len(components) == 0 and not self.options.is_compact:
            self._build_nand_circuit(context)
            return

        # Process each component
        for component_id, component in components.items():
            # Case 2: NAND gate with compact representation OR max depth reached
            if (component.identifier == 0 and self.options.is_compact) or (
                self.options.max_depth >= 0 and context.depth >= self.options.max_depth
            ):
                # Use simplified node representation
                component_ports = self._build_simple_node(
                    context, component, str(component_id)
                )
                context.add_component_ports(component_id, component_ports)
            else:
                # Case 3: Recursively build nested component
                component_context = context.create_component_context(
                    component, component_id
                )
                self._build_circuit_graph(component_context)
                context.add_component_ports(component_id, component_context.port_nodes)

    def _build_nand_circuit(self, context: CircuitBuildContext) -> None:
        """Build a NAND gate circuit with connections between ports."""
        key = f"{context.prefix}_nand"
        self.node_builder.create_nand_node(context.graph, key)

        # Connect the NAND gate to its ports
        ports = list(context.port_nodes.values())
        a, b, out = ports[0], ports[1], ports[2]
        context.graph.add_edge(pydot.Edge(a[0], key))
        context.graph.add_edge(pydot.Edge(b[0], key))
        context.graph.add_edge(pydot.Edge(key, out[0]))

    def _build_simple_node(
        self,
        context: CircuitBuildContext,
        circuit: Circuit,
        component_id: CircuitId,
    ) -> Dict[InputId, Tuple[str, str]]:
        """Build a simplified node for a circuit component
        (used for NAND gates or max depth)."""
        key = f"{context.prefix}_comp_{component_id}"

        # Create appropriate node based on circuit type
        if circuit.identifier == 0:  # NAND gate
            self.node_builder.create_nand_node(context.graph, key)
        else:  # Other circuit types
            self.node_builder.create_circuit_node(context.graph, circuit, key)

        # All ports map to the same node
        node_ports = dict.fromkeys(
            circuit.inputs.keys(), (key, str(circuit.identifier))
        )
        node_ports.update(
            dict.fromkeys(circuit.outputs.keys(), (key, str(circuit.identifier)))
        )

        return node_ports

    def _connect_all_parts(self, context: CircuitBuildContext) -> None:
        """Connect all parts of the circuit."""
        # The main graph has its I/O connections bolded
        penwidth = 2 if context.is_main_graph() and self.options.bold_io else 1

        # Connect inputs
        self._connect_circuit_inputs(context, penwidth)

        # Connect outputs
        self._connect_circuit_outputs(context, penwidth)

        # Connect between components
        self._connect_components(context)

    def _connect_circuit_inputs(
        self, context: CircuitBuildContext, penwidth: int
    ) -> None:
        """Connect circuit inputs to component inputs."""
        for circuit_input_id, input_wire in context.circuit.inputs.items():
            for component_id, component in context.circuit.components.items():
                matching_inputs = [
                    input_id
                    for input_id, wire in component.inputs.items()
                    if wire.id == input_wire.id
                ]

                for component_input_id in matching_inputs:
                    source_node = context.port_nodes[circuit_input_id]
                    target_node = context.components_ports[component_id][
                        component_input_id
                    ]
                    context.graph.add_edge(
                        pydot.Edge(source_node[0], target_node[0], penwidth=penwidth)
                    )

    def _connect_circuit_outputs(
        self, context: CircuitBuildContext, penwidth: int
    ) -> None:
        """Connect component outputs to circuit outputs."""
        for circuit_output_id, output_wire in context.circuit.outputs.items():
            for component_id, component in context.circuit.components.items():
                matching_outputs = [
                    output_id
                    for output_id, wire in component.outputs.items()
                    if wire.id == output_wire.id
                ]

                for component_output_id in matching_outputs:
                    source_node = context.components_ports[component_id][
                        component_output_id
                    ]
                    target_node = context.port_nodes[circuit_output_id]
                    context.graph.add_edge(
                        pydot.Edge(source_node[0], target_node[0], penwidth=penwidth)
                    )

    def _connect_components(self, context: CircuitBuildContext) -> None:
        """Connect component outputs to other component inputs."""
        for source_id, source in context.circuit.components.items():
            for target_id, target in context.circuit.components.items():
                if source_id == target_id:
                    continue

                for source_output_id, source_output_wire in source.outputs.items():
                    # Find all target inputs with matching wire id
                    matching_inputs = [
                        target_input_id
                        for target_input_id, target_input_wire in target.inputs.items()
                        if target_input_wire.id == source_output_wire.id
                    ]

                    for target_input_id in matching_inputs:
                        source_node = context.components_ports[source_id][
                            source_output_id
                        ]
                        target_node = context.components_ports[target_id][
                            target_input_id
                        ]
                        context.graph.add_edge(
                            pydot.Edge(source_node[0], target_node[0])
                        )


def generate_graph(circuit: Circuit, options: GraphOptions) -> pydot.Dot:
    """
    Generate a hierarchical visualization of a circuit.

    Args:
        circuit: The circuit to visualize
        options: Visualization options

    Returns:
        The generated pydot graph object
    """

    def _counter():
        count = 0
        while True:
            yield count
            count += 1

    counter = _counter()

    # WIP TODO : factorize
    def uniquify(circuit: Circuit):
        for k in list(circuit.inputs.keys()):
            new_id = f"{k}_{next(counter)}"
            circuit.inputs[new_id] = circuit.inputs.pop(k)
            circuit.inputs_names[new_id] = circuit.inputs_names.pop(k)
        for k in list(circuit.outputs.keys()):
            new_id = f"{k}_{next(counter)}"
            circuit.outputs[new_id] = circuit.outputs.pop(k)
            circuit.outputs_names[new_id] = circuit.outputs_names.pop(k)
        for component in circuit.components.values():
            if component.identifier != 0:
                component.identifier = f"{component.identifier}_{next(counter)}"
            uniquify(component)

    uniquify(circuit)

    builder = NestedGraphBuilder(options)
    return builder.build_graph(circuit)


def save_graph(graph: pydot.Dot, filename: str, format: str) -> str:
    """Save the graph to a file"""
    output_file = f"{filename}.{format}"
    graph.write(output_file, format=format)
    return output_file


# Example usage
if __name__ == "__main__":
    # Create schematics library
    schematics_builder = SchematicsBuilder()
    schematics_builder.build_circuits()
    reference = schematics_builder.schematics

    default_round_trip = DefaultDecoder().decode(DefaultEncoder().encode(reference))
    bit_packed_round_trip = BitPackedDecoder().decode(
        BitPackedEncoder().encode(reference)
    )

    # Visualize different circuits
    for schematics, schematics_type in [
        (reference, "reference"),
        (default_round_trip, "default_round_trip"),
        (bit_packed_round_trip, "bit_packed_round_trip"),
    ]:
        circuit = schematics.get_schematic_idx(7)
        graph = generate_graph(
            circuit,
            GraphOptions(is_compact=True, is_aligned=True, bold_io=True, max_depth=-1),
        )
        output_file = save_graph(
            graph,
            f"half_adder_{schematics_type}",
            "svg",
        )
        print(f"Nested graph saved to {output_file}")
