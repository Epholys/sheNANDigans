from itertools import product
import pydot
from nand.circuit import Circuit
from typing import List, Tuple, Literal

from nand.graph_node_builder import NodeBuilder

# Define type aliases for better readability
type Connection = Tuple[str, str]  # (source, destination)
type InputConnection = Connection
type OutputConnection = Connection
type InternalConnection = Connection
type AllConnections = Tuple[
    List[InputConnection], List[OutputConnection], List[InternalConnection]
]
type NandCollection = List[Tuple[str, Circuit]]


class GraphOptions:
    def __init__(self, is_nested: bool, is_aligned: bool, bold_io: bool):
        self.is_nested = is_nested
        self.is_aligned = is_aligned
        self.bold_io = bold_io


def _explore_circuit_recursive(
    circuit: Circuit,
    parent_graph: pydot.Graph,
    options: GraphOptions,
    node_builder: NodeBuilder,
    is_top_level: bool = True,
    prefix: str = "",
) -> NandCollection:
    """Recursively explore the circuit to extract all NAND gates."""
    current_graph = parent_graph
    # Create subgraph for nested circuits if needed
    if not is_top_level and options.is_nested:
        current_graph = pydot.Cluster(
            f"{prefix}_cluster",
            label=f"Circuit {circuit.identifier}",
            style="rounded,filled",
            fillcolor="#f0f0f0",
            color="#000000",
        )
        parent_graph.add_subgraph(current_graph)

    all_nands: NandCollection = []

    # Process all components in this circuit
    for component_name, component in circuit.components.items():
        node_id = f"{prefix}_{component_name}"
        if component.identifier == 0:  # NAND gate
            all_nands.append((node_id, component))
            node_builder.create_nand_node(current_graph, node_id)
        else:
            # Recursively process nested circuit
            all_nands.extend(
                _explore_circuit_recursive(
                    component, current_graph, options, node_builder, False, node_id
                )
            )

    return all_nands


class FlattenedGraphBuilder:
    def __init__(self, circuit: Circuit, options: GraphOptions):
        self.circuit = circuit
        self.options = options
        self.node_builder = NodeBuilder()
        self.graph = pydot.Dot(
            f"Raw_Circuit_{circuit.identifier}",
            graph_type="digraph",
            rankdir="LR",
            label=circuit.identifier,
        )

    def generate_graph(self) -> pydot.Dot:
        """Generate a simplified graph showing only the connections between circuit
        inputs/outputs and NAND gates, without hierarchical representation.
        """
        # Create the main graph

        # Step 1: Collect all NAND gates
        all_nands = _explore_circuit_recursive(
            self.circuit, self.graph, self.options, self.node_builder
        )

        # Step 2: Extract all connections
        all_connections = self._extract_all_connections(all_nands)

        # Step 3: Add nodes and connections to the graph
        self._add_circuit_io_nodes()
        self._add_all_connections(all_connections)

        return self.graph

    def _extract_all_connections(self, all_nands: NandCollection) -> AllConnections:
        """Extract all connections from and to circuit inputs/outputs and components'
        NAND gates.
        """
        input_connections = self._extract_input_connections(all_nands)
        output_connections = self._extract_output_connections(all_nands)
        internal_connections = self._extract_internal_connections(all_nands)

        return input_connections, output_connections, internal_connections

    def _extract_input_connections(
        self, all_nands: NandCollection
    ) -> List[InputConnection]:
        """Extract connections from nand.circuit inputs to NAND gates."""
        connections = []

        for input_name, input_wire in self.circuit.inputs.items():
            for nand_id, nand in all_nands:
                for nand_input_wire in nand.inputs.values():
                    if nand_input_wire.id == input_wire.id:
                        connections.append((f"in_{input_name}", nand_id))

        return connections

    def _extract_output_connections(
        self, all_nands: NandCollection
    ) -> List[OutputConnection]:
        """Extract connections from NAND gates to circuit outputs."""
        connections = []

        for output_name, output_wire in circuit.outputs.items():
            for nand_id, nand in all_nands:
                for nand_output_wire in nand.outputs.values():
                    if nand_output_wire.id == output_wire.id:
                        connections.append((nand_id, f"out_{output_name}"))

        return connections

    def _extract_internal_connections(
        self,
        all_nands: NandCollection,
    ) -> List[InternalConnection]:
        """Extract connections between NAND gates."""
        connections = []

        for source_id, source_nand in all_nands:
            for source_output_wire in source_nand.outputs.values():
                for destination_id, destination_nand in all_nands:
                    for destination_input_wire in destination_nand.inputs.values():
                        if destination_input_wire.id == source_output_wire.id:
                            connections.append((source_id, destination_id))

        return connections

    def _add_circuit_io_nodes(self) -> None:
        """Add input and output nodes for the main circuit."""
        # Add input nodes
        input_nodes = self._add_input_nodes()

        # Add output nodes
        output_nodes = self._add_output_nodes()

        # Align nodes if needed
        if self.options.is_aligned:
            self._align_io_nodes(input_nodes, output_nodes)

    def _add_input_nodes(
        self,
    ) -> List[str]:
        """Add input nodes to the graph and return their IDs."""
        input_nodes = []

        for input_name in self.circuit.inputs.keys():
            node_id = f"in_{input_name}"
            input_nodes.append(node_id)

            self.node_builder.create_port_node(self.graph, input_name, "in", "#aaffaa")

        return input_nodes

    def _add_output_nodes(self) -> List[str]:
        """Add output nodes to the graph and return their IDs."""
        output_nodes = []

        for output_name in circuit.outputs.keys():
            node_id = f"out_{output_name}"
            output_nodes.append(node_id)

            self.node_builder.create_port_node(
                self.graph, output_name, "out", "#ffaaaa"
            )

        return output_nodes

    def _align_io_nodes(self, input_nodes: List[str], output_nodes: List[str]) -> None:
        """Align input nodes to the left and output nodes to the right."""
        # Align input nodes to the left
        input_subgraph = pydot.Subgraph("input_subgraphs", rank="min")
        for node in input_nodes:
            input_subgraph.add_node(pydot.Node(node))
        self.graph.add_subgraph(input_subgraph)

        # Align output nodes to the right
        output_subgraph = pydot.Subgraph("output_subgraph", rank="max")
        for node in output_nodes:
            output_subgraph.add_node(pydot.Node(node))
        self.graph.add_subgraph(output_subgraph)

    def _add_all_connections(
        self,
        all_connections: AllConnections,
    ) -> None:
        """Add all connections to the graph."""
        input_connections, output_connections, internal_connections = all_connections

        # Set line width based on options
        penwidth: Literal[2] | Literal[1] = 2 if self.options.bold_io else 1

        # Add IO connections with potentially bold lines
        for source, destination in input_connections + output_connections:
            self.graph.add_edge(pydot.Edge(source, destination, penwidth=penwidth))

        # Add internal connections
        for source, destination in internal_connections:
            self.graph.add_edge(pydot.Edge(source, destination))


def save_graph(graph: pydot.Dot, filename: str, format: str) -> str:
    """Save the graph to a file."""
    output_file = f"{filename}.{format}"
    graph.write(output_file, format=format)
    return output_file


# Example usage
if __name__ == "__main__":
    import os
    from nand.schematics import SchematicsBuilder

    # Set Graphviz path if needed
    os.environ["PATH"] += os.pathsep + "C:/Program Files/Graphviz/bin"

    # Create schematics library
    schematics_builder = SchematicsBuilder()
    schematics_builder.build_circuits()
    reference = schematics_builder.schematics

    # Generate raw graphs for different circuits
    for idx in [7]:  # Visualize specific circuits
        for n, a in list(product([True, False], repeat=2)):
            try:
                circuit = reference.get_schematic_idx(idx)
                graph_builder = FlattenedGraphBuilder(
                    circuit,
                    GraphOptions(is_nested=n, is_aligned=a, bold_io=True),
                )
                graph = graph_builder.generate_graph()
                output_file = save_graph(
                    graph, f"flattened_circuit_{idx}_{n}_{a}", "svg"
                )
                print(f"Flattened graph saved to {output_file}")
            except Exception as e:
                print(f"Error visualizing circuit {idx}: {e}")
