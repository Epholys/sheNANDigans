import pydot
from circuit import Circuit


def generate_circuit_graph(circuit: Circuit, filename: str = None, format: str = "png"):
    """
    Generate a streamlined hierarchical visualization of a circuit.

    Args:
        circuit: The circuit to visualize
        filename: Optional output filename (without extension)
        format: Output format (png, svg, pdf, etc.)

    Returns:
        The generated pydot graph object
    """
    # Create the main graph
    main_graph = pydot.Dot(
        f"Circuit_{circuit.identifier}", graph_type="digraph", rankdir="LR"
    )

    # Create a mapping of wire IDs to their source and target nodes
    wire_mapping = {}

    # Build the circuit graph
    _build_circuit_graph(main_graph, circuit, "", wire_mapping)

    # Connect wires directly (bypassing intermediate nodes)
    _connect_wires_directly(main_graph, wire_mapping)

    # If filename is provided, save the graph
    if filename:
        output_file = f"{filename}.{format}"
        main_graph.write(output_file, format=format)
        print(f"Graph saved to {output_file}")

    return main_graph


def _build_circuit_graph(parent_graph, circuit, prefix, wire_mapping):
    """
    Recursively build a circuit and its components as nested subgraphs.

    Args:
        parent_graph: The parent graph to add this circuit to
        circuit: The circuit to visualize
        prefix: A prefix to make node IDs unique
        wire_mapping: Dictionary mapping wire IDs to their source and target nodes

    Returns:
        A dictionary mapping circuit port nodes to wire IDs
    """
    # Create a subgraph for this circuit
    circuit_name = f"cluster_{prefix}_{circuit.identifier}"
    subgraph = pydot.Cluster(
        circuit_name,
        label=f"Circuit {circuit.identifier}",
        style="rounded,filled",
        fillcolor="#f0f0f0",
        color="#000000",
    )

    # Track port nodes and their associated wires
    port_to_wire = {}

    # Add input nodes (but don't create edges yet)
    for in_key, wire in circuit.inputs.items():
        node_id = f"{prefix}_in_{in_key}"
        port_to_wire[("in", in_key)] = wire.id

        # Create the input node
        input_node = pydot.Node(
            node_id,
            label=f"{in_key}",
            shape="circle",
            style="filled",
            fillcolor="#aaffaa",
        )
        subgraph.add_node(input_node)

        # Register this node as a target for this wire
        if wire.id not in wire_mapping:
            wire_mapping[wire.id] = {"sources": [], "targets": []}
        wire_mapping[wire.id]["targets"].append(node_id)

    # Add output nodes (but don't create edges yet)
    for out_key, wire in circuit.outputs.items():
        node_id = f"{prefix}_out_{out_key}"
        port_to_wire[("out", out_key)] = wire.id

        # Create the output node
        output_node = pydot.Node(
            node_id,
            label=f"{out_key}",
            shape="circle",
            style="filled",
            fillcolor="#ffaaaa",
        )
        subgraph.add_node(output_node)

        # Register this node as a source for this wire
        if wire.id not in wire_mapping:
            wire_mapping[wire.id] = {"sources": [], "targets": []}
        wire_mapping[wire.id]["sources"].append(node_id)

    # Handle the special case for NAND gates
    if circuit.identifier == 0:
        # Add a node representing the NAND functionality
        nand_node_id = f"{prefix}_nand_gate"
        nand_node = pydot.Node(
            nand_node_id, label="NAND", shape="box", style="filled", fillcolor="#ccccff"
        )
        subgraph.add_node(nand_node)

        # Connect inputs directly to the NAND node
        for in_key, wire in circuit.inputs.items():
            input_node_id = f"{prefix}_in_{in_key}"
            edge = pydot.Edge(input_node_id, nand_node_id)
            parent_graph.add_edge(edge)

        # Connect the NAND node directly to the output
        for out_key, wire in circuit.outputs.items():
            output_node_id = f"{prefix}_out_{out_key}"
            edge = pydot.Edge(nand_node_id, output_node_id)
            parent_graph.add_edge(edge)

    # Add the subgraph to the parent graph
    parent_graph.add_subgraph(subgraph)

    return port_to_wire


def _connect_wires_directly(graph, wire_mapping):
    """
    Create direct connections between wire sources and targets.

    Args:
        graph: The main graph
        wire_mapping: Dictionary mapping wire IDs to their source and target nodes
    """
    for wire_id, connections in wire_mapping.items():
        sources = connections["sources"]
        targets = connections["targets"]

        # Connect each source to each target
        for source in sources:
            for target in targets:
                # Skip self-connections
                if source != target:
                    edge = pydot.Edge(source, target)
                    graph.add_edge(edge)


def visualize_schematic(circuit_id, schematics_builder, filename=None, format="png"):
    """
    Helper function to quickly visualize a schematic from your library.

    Args:
        circuit_id: ID of the circuit to visualize
        schematics_builder: Instance of SchematicsBuilder with circuits
        filename: Optional output filename (without extension)
        format: Output format (png, svg, pdf, etc.)

    Returns:
        The generated pydot graph
    """
    circuit = schematics_builder.get_schematic(circuit_id)
    return generate_circuit_graph(circuit, filename, format)


# Example usage
if __name__ == "__main__":
    import os
    import schematics

    # Set Graphviz path if needed
    os.environ["PATH"] += os.pathsep + "C:/Program Files/Graphviz/bin"

    # Create schematics library
    schematics_builder = schematics.SchematicsBuilder()
    schematics_builder.build_circuits()

    # Visualize different circuits
    visualize_schematic(0, schematics_builder, "nand_gate_streamlined")
    visualize_schematic(1, schematics_builder, "not_gate_streamlined")
    visualize_schematic(2, schematics_builder, "and_gate_streamlined")
    visualize_schematic(3, schematics_builder, "or_gate_streamlined")
    visualize_schematic(5, schematics_builder, "xor_gate_streamlined")
    visualize_schematic(6, schematics_builder, "half_adder_streamlined")
