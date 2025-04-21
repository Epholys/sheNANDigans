import seaborn
from typing import Dict, Optional
import pydot
from circuit import (
    Circuit,
    CircuitKey,
    PortKey,
    PortWireDict,
)
from schematics import SchematicsBuilder


def golden_ratio_generator(scale: int):
    """Generate a sequence of indices based on the golden ratio.

    This generator yields numbers that are evenly spaced on a 0..scale interval.
    """
    phi = (5**0.5 - 1) / 2  # Golden ratio conjugate (~0.618)
    i = 0
    while True:
        yield int(scale * ((i * phi) % 1))
        i += 1


class ColorScheme:
    """A color scheme for circuit components.

    This class generates a color palette for circuit components using the golden ratio.
    It ensures that the colors are evenly spaced and visually distinct.
    """

    # The size of the color palette
    PALETTE_SIZE = 32

    def __init__(self):
        self._colors: Dict[CircuitKey, str] = {}
        self._generator = golden_ratio_generator(self.PALETTE_SIZE)
        self._palette = seaborn.husl_palette(
            n_colors=self.PALETTE_SIZE, s=0.95, l=0.8, h=0.5
        ).as_hex()

    def get_color(self, id: CircuitKey) -> str:
        """Get a color for a given circuit component ID.
        If the color has already been assigned, return the existing color.
        """
        if id in self._colors:
            return self._colors[id]
        color = self._palette[next(self._generator)]
        self._colors[id] = color
        return color


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


# A mapping between a circuit's ports and its graph node ID
type CircuitPorts = dict[PortKey, str]
# A mapping between circuit components and their ports
type ComponentsPorts = dict[CircuitKey, CircuitPorts]


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
        self.circuit_ports: CircuitPorts = {}
        self.components_ports: ComponentsPorts = {}

    def create_component_context(
        self, component: Circuit, component_name: CircuitKey
    ) -> "CircuitBuildContext":
        """Create a new context for a component."""
        # Unique prefix for the component
        # This prefix is used to create unique node IDs for the component's ports
        component_prefix = f"{self.prefix}_comp_{component_name}"

        # Build a new subgraph for the component
        graph = pydot.Cluster(
            f"cluster_{component_prefix}",
            label=f"Circuit {component.identifier}",
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

    def add_component_ports(
        self, component_name: CircuitKey, ports: CircuitPorts
    ) -> None:
        """Add all ports for a component."""
        self.components_ports[component_name] = ports

    def is_main_graph(self) -> bool:
        """Check if this is the main graph context."""
        return self.parent_context is None

    def add_subgraph_to_parent(self) -> None:
        """Add this context's graph to its parent graph."""
        if self.parent_context and self.graph != self.parent_context.graph:
            self.parent_context.graph.add_subgraph(self.graph)


class NodeBuilder:
    """Handles the creation of graph nodes for circuits and components."""

    def __init__(self, color_scheme: ColorScheme):
        self.color_scheme = color_scheme

    def create_port_node(
        self, graph: pydot.Graph, port_key: CircuitKey, prefix: str, color: str
    ) -> str:
        """Create a node for a circuit port."""
        node_id = f"{prefix}_{port_key}"
        graph.add_node(
            pydot.Node(
                node_id,
                label=f"{port_key}",
                shape="circle",
                style="filled",
                fillcolor=color,
            )
        )
        return node_id

    def create_nand_node(self, graph: pydot.Graph, name: str) -> None:
        """Create a node for a NAND gate."""
        graph.add_node(
            pydot.Node(
                name,
                label="NAND",
                shape="box",
                style="filled",
                fillcolor="#ccccff",
            )
        )

    def create_circuit_node(
        self, graph: pydot.Graph, circuit: Circuit, name: str
    ) -> None:
        """Create a node for a circuit component."""
        graph.add_node(
            pydot.Node(
                name,
                label=circuit.identifier,
                shape="component",
                style="filled",
                fillcolor=self.color_scheme.get_color(circuit.identifier),
            )
        )


class CircuitGraphBuilder:
    """Main class for building circuit graphs."""

    def __init__(self, options: GraphOptions):
        self.options = options
        self.node_builder = NodeBuilder(ColorScheme())

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
                f"{context.prefix}_in",
                "#aaffaa",
                "min",
            )
            self._add_aligned_ports(
                context,
                context.circuit.outputs,
                f"{context.prefix}_out",
                "#ffaaaa",
                "max",
            )
        else:
            self._add_ports(
                context, context.circuit.inputs, f"{context.prefix}_in", "#aaffaa"
            )
            self._add_ports(
                context, context.circuit.outputs, f"{context.prefix}_out", "#ffaaaa"
            )

    def _add_ports(
        self, context: CircuitBuildContext, ports: PortWireDict, prefix: str, color: str
    ) -> CircuitPorts:
        """Add port nodes to the graph."""
        circuit_ports: CircuitPorts = {}
        for port in ports.keys():
            node_id = self.node_builder.create_port_node(
                context.graph, port, prefix, color
            )
            circuit_ports[port] = node_id
        context.circuit_ports.update(circuit_ports)
        return circuit_ports

    def _add_aligned_ports(
        self,
        context: CircuitBuildContext,
        ports: PortWireDict,
        prefix: str,
        color: str,
        rank: str,
    ) -> None:
        """Add port nodes to the graph with rank alignment."""
        circuit_ports = self._add_ports(context, ports, prefix, color)

        # Create a subgraph to align the ports
        subgraph_name = f"{prefix}_aligned_{rank}"
        subgraph = pydot.Subgraph(subgraph_name, rank=rank)

        for node_id in circuit_ports.values():
            subgraph.add_node(pydot.Node(node_id))

        context.graph.add_subgraph(subgraph)

    def _build_components(self, context: CircuitBuildContext) -> None:
        """Build all components in the circuit."""
        components = context.circuit.components

        # Case 1: We're at a NAND gate leaf node and not using compact representation
        if len(components) == 0 and not self.options.is_compact:
            self._build_nand_circuit(context)
            return

        # Process each component
        for component_name, component in components.items():
            # Case 2: NAND gate with compact representation OR max depth reached
            if (component.identifier == 0 and self.options.is_compact) or (
                self.options.max_depth >= 0 and context.depth >= self.options.max_depth
            ):
                # Use simplified node representation
                component_ports = self._build_simple_node(
                    context, component, component_name
                )
                context.add_component_ports(component_name, component_ports)
            else:
                # Case 3: Recursively build nested component
                component_context = context.create_component_context(
                    component, component_name
                )
                self._build_circuit_graph(component_context)
                context.add_component_ports(
                    component_name, component_context.circuit_ports
                )

    def _build_nand_circuit(self, context: CircuitBuildContext) -> None:
        """Build a NAND gate circuit with connections between ports."""
        name = f"{context.prefix}_nand"
        self.node_builder.create_nand_node(context.graph, name)

        # Connect the NAND gate to its ports
        ports = list(context.circuit_ports.values())
        a, b, out = ports[0], ports[1], ports[2]
        context.graph.add_edge(pydot.Edge(a, name))
        context.graph.add_edge(pydot.Edge(b, name))
        context.graph.add_edge(pydot.Edge(name, out))

    def _build_simple_node(
        self, context: CircuitBuildContext, circuit: Circuit, component_name: CircuitKey
    ) -> Dict[CircuitKey, str]:
        """Build a simplified node for a circuit component
        (used for NAND gates or max depth)."""
        name = f"{context.prefix}_comp_{component_name}"

        # Create appropriate node based on circuit type
        if circuit.identifier == 0:  # NAND gate
            self.node_builder.create_nand_node(context.graph, name)
        else:  # Other circuit types
            self.node_builder.create_circuit_node(context.graph, circuit, name)

        # All ports map to the same node
        node_ports = {port: name for port in circuit.inputs.keys()}
        node_ports.update({port: name for port in circuit.outputs.keys()})

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
        for circuit_input_name, input_wire in context.circuit.inputs.items():
            for component_name, component in context.circuit.components.items():
                matching_inputs = [
                    input_name
                    for input_name, wire in component.inputs.items()
                    if wire.id == input_wire.id
                ]

                for component_input_name in matching_inputs:
                    source_node = context.circuit_ports[circuit_input_name]
                    target_node = context.components_ports[component_name][
                        component_input_name
                    ]
                    context.graph.add_edge(
                        pydot.Edge(source_node, target_node, penwidth=penwidth)
                    )

    def _connect_circuit_outputs(
        self, context: CircuitBuildContext, penwidth: int
    ) -> None:
        """Connect component outputs to circuit outputs."""
        for circuit_output_name, output_wire in context.circuit.outputs.items():
            for component_name, component in context.circuit.components.items():
                matching_outputs = [
                    output_name
                    for output_name, wire in component.outputs.items()
                    if wire.id == output_wire.id
                ]

                for component_output_name in matching_outputs:
                    source_node = context.components_ports[component_name][
                        component_output_name
                    ]
                    target_node = context.circuit_ports[circuit_output_name]
                    context.graph.add_edge(
                        pydot.Edge(source_node, target_node, penwidth=penwidth)
                    )

    def _connect_components(self, context: CircuitBuildContext) -> None:
        """Connect component outputs to other component inputs."""
        for source_name, source in context.circuit.components.items():
            for target_name, target in context.circuit.components.items():
                if source_name == target_name:
                    continue

                for source_output_name, source_output_wire in source.outputs.items():
                    # Find all target inputs with matching wire id
                    matching_inputs = [
                        target_input_name
                        for target_input_name, target_input_wire in target.inputs.items()
                        if target_input_wire.id == source_output_wire.id
                    ]

                    for target_input_name in matching_inputs:
                        source_node = context.components_ports[source_name][
                            source_output_name
                        ]
                        target_node = context.components_ports[target_name][
                            target_input_name
                        ]
                        context.graph.add_edge(pydot.Edge(source_node, target_node))


def generate_graph(circuit: Circuit, options: GraphOptions) -> pydot.Dot:
    """
    Generate a hierarchical visualization of a circuit.

    Args:
        circuit: The circuit to visualize
        options: Visualization options

    Returns:
        The generated pydot graph object
    """
    builder = CircuitGraphBuilder(options)
    return builder.build_graph(circuit)


def save_graph(graph: pydot.Dot, filename: str, format: str) -> str:
    """Save the graph to a file"""
    output_file = f"{filename}.{format}"
    graph.write(output_file, format=format)
    return output_file


# Example usage
if __name__ == "__main__":
    import os

    # Set Graphviz path if needed
    os.environ["PATH"] += os.pathsep + "C:/Program Files/Graphviz/bin"

    # Create schematics library
    schematics_builder = SchematicsBuilder()
    schematics_builder.build_circuits()
    reference = schematics_builder.schematics

    # Visualize different circuits
    for idx in range(10, 11):
        for depth in range(0, 3):
            circuit = reference.get_schematic_idx(idx)
            graph = generate_graph(
                circuit,
                GraphOptions(
                    is_compact=True, is_aligned=True, bold_io=True, max_depth=depth
                ),
            )
            output_file = save_graph(
                graph,
                f"circuit_{idx}_{depth}",
                "svg",
            )
            print(f"Nested graph saved to {output_file}")
