import pydot
from circuit import Circuit, CircuitDict
from schematics import get_schematic_idx
from typing import List, Literal, Tuple


class GraphOptions:
    def __init__(self, is_nested: bool, is_aligned: bool, bold_io: bool):
        self.is_nested = is_nested
        self.is_aligned = is_aligned
        self.bold_ins_outs = bold_io


def generate_circuit_graph(
    circuit: Circuit, options: GraphOptions, filename: str, format: str = "png"
) -> pydot.Graph:
    """
    Generate a simplified graph showing only the connections between circuit inputs/outputs
    and NAND gates, without hierarchical representation.

    Args:
        circuit: The circuit to visualize
        filename: Output filename (without extension)
        format: Output format (png, svg, pdf, etc.)

    Returns:
        The generated pydot graph object
    """
    # Create the main graph
    graph = pydot.Dot(
        f"Raw_Circuit_{circuit.identifier}",
        graph_type="digraph",
        rankdir="LR",
        label=circuit.identifier,
    )

    # Extract all components and connections
    all_components, input_connections, output_connections, internal_connections = (
        _extract_circuit_details(circuit, graph, options)
    )

    # Add all nodes to the graph
    _add_circuit_io_nodes(graph, circuit, options)
    # _add_component_nodes(graph, all_components)

    # Add all connections
    _add_all_connections(
        graph, input_connections, output_connections, internal_connections, options
    )

    # Save the graph
    output_file = f"{filename}.{format}"
    graph.write(output_file, format=format)
    print(f"Raw graph saved to {output_file}")

    return graph


def _extract_circuit_details(
    circuit: Circuit, graph: pydot.Graph, options: GraphOptions
) -> Tuple[
    List[Tuple[str, Circuit]],  # all_components
    List[Tuple[str, str, int]],  # input_connections (input_id, component_id, wire_id)
    List[Tuple[str, str, int]],  # output_connections (component_id, output_id, wire_id)
    List[
        Tuple[str, str, int]
    ],  # internal_connections (from_component, to_component, wire_id)
]:
    """
    Extracts all components and their connections from a circuit.
    Flattens the hierarchy to get only NAND gates and connections.
    """
    # Gather all components (including nested ones)
    all_nands: List[Tuple[str, Circuit]] = []
    input_connections: List[Tuple[str, str, int]] = []
    output_connections: List[Tuple[str, str, int]] = []
    internal_connections: List[Tuple[str, str, int]] = []

    def _explore_circuit(
        circuit: Circuit,
        graph: pydot.Graph,
        must_nest: bool,
        first_call: bool = True,
        prefix: str = "",
    ):
        """Recursively explore the circuit to extract all NAND gates and connections"""
        # Process nested components
        parent_graph = graph
        if not first_call and must_nest:
            graph = pydot.Cluster(
                f"{prefix}_cluster",
                label=f"Circuit {circuit.identifier}",
                style="rounded,filled",
                fillcolor="#f0f0f0",
                color="#000000",
            )

        for component_name, component in circuit.components.items():
            name = f"{prefix}_{component_name}"

            if component.identifier == 0:  # NAND gate
                all_nands.append((name, component))
                _add_nand_node(graph, name)
            else:
                _explore_circuit(component, graph, options.is_nested, False, name)

        if not first_call and must_nest:
            parent_graph.add_subgraph(graph)

    # First pass: gather all NAND components
    _explore_circuit(circuit, graph, True)

    # Second pass: Extract main circuit input connections
    for in_name, in_wire in circuit.inputs.items():
        # Find components that use this input wire
        for comp_id, comp in all_nands:
            for comp_in_name, comp_in_wire in comp.inputs.items():
                if comp_in_wire.id == in_wire.id and in_wire.id:
                    input_connections.append((f"in_{in_name}", comp_id, in_wire.id))

    # Third pass: Extract main circuit output connections
    for out_name, out_wire in circuit.outputs.items():
        # Find components that produce this output wire
        for comp_id, comp in all_nands:
            for comp_out_name, comp_out_wire in comp.outputs.items():
                if comp_out_wire.id == out_wire.id and out_wire.id:
                    output_connections.append((comp_id, f"out_{out_name}", out_wire.id))

    # Fourth pass: Extract internal connections between components
    for src_id, src_comp in all_nands:
        for src_out_name, src_out_wire in src_comp.outputs.items():
            for dst_id, dst_comp in all_nands:
                if src_id != dst_id:  # Don't connect to self
                    for dst_in_name, dst_in_wire in dst_comp.inputs.items():
                        if dst_in_wire.id == src_out_wire.id and src_out_wire.id:
                            internal_connections.append(
                                (src_id, dst_id, src_out_wire.id)
                            )

    return all_nands, input_connections, output_connections, internal_connections


def _add_circuit_io_nodes(graph: pydot.Graph, circuit: Circuit, options: GraphOptions):
    """Add input and output nodes for the main circuit"""
    # Add input nodes
    input_nodes = []
    for in_name in circuit.inputs.keys():
        node = f"in_{in_name}"
        input_nodes.append(node)
        graph.add_node(
            pydot.Node(
                node,
                label=f"{in_name}",
                shape="circle",
                style="filled",
                fillcolor="#aaffaa",
            )
        )
    if options.is_aligned:
        input_subgraph = pydot.Subgraph("input_subgraphs", rank="min")
        for node in input_nodes:
            input_subgraph.add_node(pydot.Node(node))
        graph.add_subgraph(input_subgraph)

    # Add output nodes
    output_nodes = []
    for out_name in circuit.outputs.keys():
        node = f"out_{out_name}"
        output_nodes.append(node)
        graph.add_node(
            pydot.Node(
                node,
                label=f"{out_name}",
                shape="circle",
                style="filled",
                fillcolor="#ffaaaa",
            )
        )
    if options.is_aligned:
        output_subgraph = pydot.Subgraph("output_subgraph", rank="max")
        for node in output_nodes:
            output_subgraph.add_node(pydot.Node(node))
        graph.add_subgraph(output_subgraph)


def _add_component_nodes(graph: pydot.Graph, components: List[Tuple[str, Circuit]]):
    """Add nodes for all components (NAND gates)"""
    for comp_id, comp in components:
        graph.add_node(
            pydot.Node(
                comp_id,
                label="NAND",
                shape="box",
                style="filled",
                fillcolor="#ccccff",
            )
        )


def _add_nand_node(graph: pydot.Graph, id: str):
    """Add nodes for all components (NAND gates)"""
    graph.add_node(
        pydot.Node(
            id,
            label="NAND",
            shape="box",
            style="filled",
            fillcolor="#ccccff",
        )
    )


def _add_all_connections(
    graph: pydot.Graph,
    input_connections: List[Tuple[str, str, int]],
    output_connections: List[Tuple[str, str, int]],
    internal_connections: List[Tuple[str, str, int]],
    options: GraphOptions,
):
    penwidth: Literal[2] | Literal[1] = 2 if options.bold_ins_outs else 1

    """Add all connections to the graph"""
    # Add connections from inputs to components
    for src, dst, _ in input_connections:
        graph.add_edge(pydot.Edge(src, dst, penwidth=penwidth))

    # Add connections from components to outputs
    for src, dst, _ in output_connections:
        graph.add_edge(pydot.Edge(src, dst, penwidth=penwidth))

    # Add connections between components
    for src, dst, _ in internal_connections:
        graph.add_edge(pydot.Edge(src, dst))


def visualize_schematic(
    circuit_idx: int,
    options: GraphOptions,
    schematics: CircuitDict,
    filename: str,
    format: str = "png",
) -> pydot.Graph:
    """
    Helper function to quickly visualize a raw schematic from your library.

    Args:
        circuit_idx: Index of the circuit to visualize
        schematics: Dictionary of circuits
        filename: Output filename (without extension)
        format: Output format (png, svg, pdf, etc.)

    Returns:
        The generated pydot graph
    """
    circuit = get_schematic_idx(circuit_idx, schematics)
    return generate_circuit_graph(circuit, options, filename, format)


# Example usage
if __name__ == "__main__":
    import os
    from schematics import SchematicsBuilder

    # Set Graphviz path if needed
    os.environ["PATH"] += os.pathsep + "C:/Program Files/Graphviz/bin"

    # Create schematics library
    schematics_builder = SchematicsBuilder()
    schematics_builder.build_circuits()
    reference = schematics_builder.schematics

    # Generate raw graphs for different circuits
    for idx in [5, 6, 7, 8, 10]:  # Visualize first 9 circuits
        try:
            visualize_schematic(
                idx,
                GraphOptions(is_nested=False, is_aligned=True, bold_io=True),
                reference,
                f"raw_circuit_{idx}",
                "svg",
            )
        except Exception as e:
            print(f"Error visualizing circuit {idx}: {e}")
