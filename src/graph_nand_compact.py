from ast import Dict
from enum import Enum, auto
from typing import Any, Tuple
import pydot
from circuit import Circuit, CircuitDict, CircuitKey
from decoding import CircuitDecoder
from encoding import CircuitEncoder
from schematics import SchematicsBuilder, get_schematic_idx

def generate_circuit_graph(circuit: Circuit, filename: str, format: str = "png") -> pydot.Graph:
    """
    Generate a hierarchical visualization of a circuit.

    Args:
        circuit: The circuit to visualize
        filename: Optional output filename (without extension)
        format: Output format (png, svg, pdf, etc.)

    Returns:
        The generated pydot graph object
    """
    # Create the main graph
    graph = pydot.Dot(
        f"Circuit_{circuit.identifier}", graph_type="digraph", rankdir="LR"
    )

    # Create the circuit representation directly (not as a subgraph)
    _build_circuit_graph(graph, circuit, "")

    # If filename is provided, save the graph
    output_file = f"{filename}.{format}"
    graph.write(output_file, format=format)
    print(f"Graph saved to {output_file}")

    return graph


def _build_circuit_graph(parent_graph: pydot.Graph, circuit: Circuit, prefix: str):
    """
    Recursively build a circuit and its components as nested subgraphs.

    Args:
        parent_graph: The parent graph to add this circuit to
        circuit: The circuit to visualize
        prefix: A prefix to make node IDs unique

    Returns:
        A dictionary mapping (port_type, port_key) to node_id
    """
    # Create nodes for this level

    ports: dict[CircuitKey, str] = {}

    circuit_name = f"cluster_{prefix}_{circuit.identifier}"
    graph = pydot.Cluster(
        circuit_name,
        label=f"Circuit {circuit.identifier}",
        style="rounded,filled",
        fillcolor="#f0f0f0",
        color="#000000",
    )

    # Add input nodes
    for in_key, wire in circuit.inputs.items():
        node_id = f"{prefix}_in_{in_key}"
        ports[in_key] = node_id
        graph.add_node(
            pydot.Node(
                node_id,
                label=f"{in_key}",
                shape="circle",
                style="filled",
                fillcolor="#aaffaa",
            )
        )

    # Add output nodes
    for out_key, wire in circuit.outputs.items():
        node_id = f"{prefix}_out_{out_key}"
        ports[out_key] = node_id
        graph.add_node(
            pydot.Node(
                node_id,
                label=f"{out_key}",
                shape="circle",
                style="filled",
                fillcolor="#ffaaaa",
            )
        )

    # Process all component circuits recursively
    component_ports : dict[CircuitKey, Any] = {}

    # Build all component subgraphs
    for comp_key, component in circuit.components.items():
        comp_prefix = f"{prefix}_comp_{comp_key}"

        # If component is a NAND gate, add its nodes directly to this graph
        # (not as a subgraph) while maintaining proper connections
        if component.identifier == 0:
            # Create a simple NAND gate node
            nand_node_id = f"{comp_prefix}_nand_gate"
            graph.add_node(
                pydot.Node(
                    nand_node_id,
                    label="NAND",
                    shape="box",
                    style="filled",
                    fillcolor="#ccccff",
                )
            )

            # Create a mapping for this component's ports
            component_port_nodes = {
                in_key: nand_node_id for in_key in component.inputs.keys()
            }
            component_port_nodes.update(
                {out_key: nand_node_id for out_key in component.outputs.keys()}
            )
            component_ports[comp_key] = component_port_nodes
        else:
            # For non-NAND components, process them recursively as subgraphs
            component_ports[comp_key] = _build_circuit_graph(
                graph, component, comp_prefix
            )

    # Create direct connections between circuit inputs and component inputs
    for input, wire in circuit.inputs.items():
        wire_id = wire.id

        # Connect to all matching component inputs
        for comp_key, component in circuit.components.items():
            for comp_in_key, comp_wire in component.inputs.items():
                if comp_wire.id == wire_id:
                    # For NAND gates, connect directly to the NAND node
                    if component.identifier == 0:
                        target_node = component_ports[comp_key][comp_in_key]
                    else:
                        target_node = component_ports[comp_key][comp_in_key]

                    parent_graph.add_edge(
                        pydot.Edge(ports[input], target_node)
                    )

    # Connect component outputs to circuit outputs
    for circuit_out_key, wire in circuit.outputs.items():
        wire_id = wire.id

        # Find which component produces this output
        for comp_key, component in circuit.components.items():
            for comp_out_key, comp_wire in component.outputs.items():
                if comp_wire.id == wire_id:
                    source_node = component_ports[comp_key][comp_out_key]

                    parent_graph.add_edge(
                        pydot.Edge(source_node, ports[circuit_out_key])
                    )

    # Connect component outputs to other component inputs
    for src_comp_key, src_component in circuit.components.items():
        for src_out_key, src_wire in src_component.outputs.items():
            src_wire_id = src_wire.id

            # Find all components that use this wire as input
            for tgt_comp_key, tgt_component in circuit.components.items():
                for tgt_in_key, tgt_wire in tgt_component.inputs.items():
                    if tgt_wire.id == src_wire_id:
                        source_node = component_ports[src_comp_key][
                            src_out_key
                        ]

                        target_node = component_ports[tgt_comp_key][tgt_in_key]

                        parent_graph.add_edge(pydot.Edge(source_node, target_node))

    # Add the subgraph to the parent graph if this is not the main circuit
    parent_graph.add_subgraph(graph)

    return ports


def visualize_schematic(circuit_idx : int, schematics : CircuitDict, filename : str, format : str ="png") -> pydot.Graph:
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
    circuit = get_schematic_idx(circuit_idx, schematics)
    return generate_circuit_graph(circuit, filename, format)


# Example usage
if __name__ == "__main__":
    import os

    # Set Graphviz path if needed
    os.environ["PATH"] += os.pathsep + "C:/Program Files/Graphviz/bin"

    # Create schematics library
    schematics_builder = SchematicsBuilder()
    schematics_builder.build_circuits()
    reference = schematics_builder.schematics

    encoder = CircuitEncoder(reference.copy())
    encoded = encoder.encode()
    decoder = CircuitDecoder(encoded.copy())
    round_trip_1 = decoder.decode()

    encoder = CircuitEncoder(round_trip_1.copy())
    encoded = encoder.encode()
    decoder = CircuitDecoder(encoded.copy())
    round_trip_2 = decoder.decode()

    # Visualize different circuits
    # visualize_schematic(0, reference, "nand_gate_better_nand")
    # visualize_schematic(1, reference, "not_gate_better_nand")
    # visualize_schematic(2, reference, "and_gate_better_nand")
    # visualize_schematic(3, reference, "or_gate_better_nand")
    # visualize_schematic(5, reference, "xor_gate_better_nand")
    # visualize_schematic(6, reference, "half_adder_better_nand")
    # visualize_schematic(7, reference, "fulladder_nand")
    visualize_schematic(8, reference, "2bitsadder_better_nand_refact", "svg")
    # visualize_schematic(8, round_trip_1, "2bitsadder_roundtrip_1_better_nand")
    # visualize_schematic(8, round_trip_2, "2bitsadder_roundtrip_2_better_nand")
