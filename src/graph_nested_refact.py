import seaborn
from typing import Dict, Optional
import pydot
from circuit import (
    Circuit,
    CircuitKey,
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
    PALETTE_SIZE = 256

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


class CircuitBuildContext:
    """Context for building a circuit graph."""

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

        # Port mappings
        self.circuit_ports: Dict[CircuitKey, str] = {}
        self.components_ports: Dict[CircuitKey, Dict[CircuitKey, str]] = {}

    def create_component_context(
        self, component: Circuit, component_name: CircuitKey
    ) -> "CircuitBuildContext":
        """Create a new context for a component."""
        component_prefix = f"{self.prefix}_comp_{component_name}"

        # If this is a cluster subgraph, create it
        if self.depth > 0 or component.components:
            graph = pydot.Cluster(
                f"cluster_{component_prefix}_{component.identifier}",
                label=f"Circuit {component.identifier}",
                style="rounded,filled",
                fillcolor="#f0f0f0",
                color="#000000",
            )
        else:
            graph = self.graph

        return CircuitBuildContext(
            circuit=component,
            graph=graph,
            prefix=component_prefix,
            depth=self.depth + 1,
            parent_context=self,
        )

    def add_component_ports(
        self, component_name: CircuitKey, ports: Dict[CircuitKey, str]
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
                fillcolor=self.color_scheme.get_color(circuit.identifier),
            )
        )


class CircuitGraphBuilder:
    """Main class for building circuit graphs."""

    def __init__(self, options: GraphOptions):
        self.options = options
        self.color_scheme = ColorScheme()
        self.node_builder = NodeBuilder(self.color_scheme)

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
    ) -> None:
        """Add port nodes to the graph."""
        for port in ports.keys():
            node_id = self.node_builder.create_port_node(
                context.graph, port, prefix, color
            )
            context.circuit_ports[port] = node_id

    def _add_aligned_ports(
        self,
        context: CircuitBuildContext,
        ports: PortWireDict,
        prefix: str,
        color: str,
        rank: str,
    ) -> None:
        """Add port nodes to the graph with rank alignment."""
        self._add_ports(context, ports, prefix, color)

        # Create a subgraph to align the ports
        subgraph_name = f"aligned_{rank}_{prefix}"
        subgraph = pydot.Subgraph(subgraph_name, rank=rank)

        for port, node_id in context.circuit_ports.items():
            if node_id.startswith(f"{prefix}_"):
                subgraph.add_node(pydot.Node(node_id))

        context.graph.add_subgraph(subgraph)

    def _build_components(self, context: CircuitBuildContext) -> None:
        """Build all components in the circuit."""
        components = context.circuit.components

        if len(components) == 0 and not self.options.is_compact:
            # We are at the NAND level
            self._build_nand_circuit(context)
            return

        for component_name, component in components.items():
            # TODO : coalesce ?
            if component.identifier == 0 and self.options.is_compact:
                # Compact NAND representation
                component_ports = self._build_nand_component(
                    context, component, component_name
                )
                context.add_component_ports(component_name, component_ports)
            elif self.options.max_depth > 0 and context.depth >= self.options.max_depth:
                # Max depth reached, use simplified node
                component_ports = self._build_node(context, component, component_name)
                context.add_component_ports(component_name, component_ports)
            else:
                # Create a new context for this component
                component_context = context.create_component_context(
                    component, component_name
                )

                # Build the component recursively
                self._build_circuit_graph(component_context)

                # Store the component's ports in the parent context
                context.add_component_ports(
                    component_name, component_context.circuit_ports
                )

    def _build_nand_circuit(self, context: CircuitBuildContext) -> None:
        """Build a NAND gate circuit."""
        name = f"{context.prefix}_nand"
        self.node_builder.create_nand_node(context.graph, name)

        ports = list(context.circuit_ports.values())
        a, b, out = ports[0], ports[1], ports[2]
        context.graph.add_edge(pydot.Edge(a, name))
        context.graph.add_edge(pydot.Edge(b, name))
        context.graph.add_edge(pydot.Edge(out, name))

    def _build_nand_component(
        self, context: CircuitBuildContext, nand: Circuit, component_name: CircuitKey
    ) -> Dict[CircuitKey, str]:
        """Build a compact NAND component."""
        name = f"{context.prefix}_comp_{component_name}"
        self.node_builder.create_nand_node(context.graph, name)

        # All ports map to the same node
        nand_ports = {in_key: name for in_key in nand.inputs.keys()}
        nand_ports.update({out_key: name for out_key in nand.outputs.keys()})

        return nand_ports

    def _build_node(
        self, context: CircuitBuildContext, circuit: Circuit, component_name: CircuitKey
    ) -> Dict[CircuitKey, str]:
        """Build a simplified node for a circuit component."""
        # TODO coalesce w/ _build_nand_component ?
        name = f"{context.prefix}_comp_{component_name}"
        self.node_builder.create_circuit_node(context.graph, circuit, name)

        # All ports map to the same node
        node_ports = {in_key: name for in_key in circuit.inputs.keys()}
        node_ports.update({out_key: name for out_key in circuit.outputs.keys()})

        return node_ports

    def _connect_all_parts(self, context: CircuitBuildContext) -> None:
        """Connect all parts of the circuit."""
        # Determine penwidth for I/O connections
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
        circuit = context.circuit
        circuit_ports = context.circuit_ports
        components_ports = context.components_ports

        for circuit_input_name, input_wire in circuit.inputs.items():
            for component_name, component in circuit.components.items():
                matching_inputs = [
                    input_name
                    for input_name, wire in component.inputs.items()
                    if wire.id == input_wire.id
                ]

                for component_input_name in matching_inputs:
                    source_node = circuit_ports[circuit_input_name]
                    target_node = components_ports[component_name][component_input_name]
                    context.graph.add_edge(
                        pydot.Edge(source_node, target_node, penwidth=penwidth)
                    )

    def _connect_circuit_outputs(
        self, context: CircuitBuildContext, penwidth: int
    ) -> None:
        """Connect component outputs to circuit outputs."""
        circuit = context.circuit
        circuit_ports = context.circuit_ports
        components_ports = context.components_ports

        for circuit_output_name, output_wire in circuit.outputs.items():
            for component_name, component in circuit.components.items():
                matching_outputs = [
                    output_name
                    for output_name, wire in component.outputs.items()
                    if wire.id == output_wire.id
                ]

                for component_output_name in matching_outputs:
                    source_node = components_ports[component_name][
                        component_output_name
                    ]
                    target_node = circuit_ports[circuit_output_name]
                    context.graph.add_edge(
                        pydot.Edge(source_node, target_node, penwidth=penwidth)
                    )

    def _connect_components(self, context: CircuitBuildContext) -> None:
        """Connect component outputs to other component inputs."""
        circuit = context.circuit
        components_ports = context.components_ports

        for source_name, source in circuit.components.items():
            for target_name, target in circuit.components.items():
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
                        source_node = components_ports[source_name][source_output_name]
                        target_node = components_ports[target_name][target_input_name]
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
    for depth in range(3, 4):
        circuit = reference.get_schematic_idx(10)
        graph = generate_graph(
            circuit,
            GraphOptions(
                is_compact=True, is_aligned=True, bold_io=True, max_depth=depth
            ),
        )
        output_file = save_graph(
            graph,
            f"circuit_{10}_{depth}",
            "svg",
        )
        print(f"Nested graph saved to {output_file}")
