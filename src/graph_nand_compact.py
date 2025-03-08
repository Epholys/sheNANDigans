from ast import Dict
from enum import Enum, auto
from typing import Any, Tuple, TypeAlias
import pydot
from circuit import Circuit, CircuitDict, CircuitKey, InputKey, InputWireDict, PortWireDict
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

type CircuitPorts = dict[CircuitKey, str]
type ComponentsPorts = dict[CircuitKey, CircuitPorts]

def _build_circuit_graph(parent_graph: pydot.Graph, circuit: Circuit, prefix: str) -> CircuitPorts:
    """
    Recursively build a circuit and its components as nested subgraphs.

    Args:
        parent_graph: The parent graph to add this circuit to
        circuit: The circuit to visualize
        prefix: A prefix to make node IDs unique

    Returns:
        A dictionary mapping (port_type, port_key) to node_id
    """
    # A port is an input or output of a circuit
    # ports maps the input/output key to the Node ID

    circuit_name = f"cluster_{prefix}_{circuit.identifier}"
    graph = pydot.Cluster(
        circuit_name,
        label=f"Circuit {circuit.identifier}",
        style="rounded,filled",
        fillcolor="#f0f0f0",
        color="#000000",
    )

    circuit_ports: CircuitPorts = {}

    # Add ports nodes
    circuit_ports.update(_add_ports_nodes(circuit.inputs, graph, f"{prefix}_in", "#aaffaa"))
    circuit_ports.update(_add_ports_nodes(circuit.outputs, graph, f"{prefix}_out", "#ffaaaa"))

    # A mapping between all the components and their ports
    components_ports : ComponentsPorts = _build_components_graph(circuit.components, graph, prefix)
    
    # Create connections between circuit inputs and component inputs.
    # For each input in the circuit, search in all components the corresponding input wire.
    _connect_inputs(circuit, circuit_ports, components_ports, graph)

    # Connect component outputs to circuit outputs.
    # For each output in the circuit, search in all components the corresponding output wire.
    _connect_outputs(circuit, circuit_ports, components_ports, graph)


    # Connect component outputs to other component inputs.
    # For each components' output, search in all components the corresponding input wire.
    _connect_components(circuit, circuit_ports, components_ports, graph)


    # Add the subgraph to the parent graph if this is not the main circuit
    parent_graph.add_subgraph(graph)

    return circuit_ports

def _add_ports_nodes(ports: PortWireDict, graph: pydot.Graph, prefix: str, color: str) -> CircuitPorts:
    port_node_ids: CircuitPorts = {}
    for port in ports.keys():
        node_id = f"{prefix}_{port}"
        port_node_ids[port] = node_id
        graph.add_node(
            pydot.Node(
                node_id,
                label=f"{port}",
                shape="circle",
                style="filled",
                fillcolor=color,
            )
        )
    return port_node_ids

def _build_components_graph(components: CircuitDict, graph: pydot.Graph, prefix: str) -> ComponentsPorts:
    component_ports: ComponentsPorts = {}
    
    for component_name, component in components.items():
        component_prefix = f"{prefix}_comp_{component_name}"

        if component.identifier == 0:
            # If component is a NAND gate, add itself as a node directly to this graph
            component_ports[component_name] = _build_nand_node(component, graph, component_prefix)
        else:
            # For non-NAND components, process them recursively.
            component_ports[component_name] = _build_circuit_graph(
                graph, component, component_prefix
            )
    
    return component_ports


def _build_nand_node(nand: Circuit, graph: pydot.Graph, name : str) -> CircuitPorts:
    graph.add_node(
        pydot.Node(
            name,
            label="NAND",
            shape="box",
            style="filled",
            fillcolor="#ccccff",
        )
    )

    # As it is a compact graph, the inputs and outputs of NAND gates are "collapsed" into the gate itself
    nand_ports : CircuitPorts = {
        in_key: name for in_key in nand.inputs.keys()
    }
    nand_ports.update(
        {out_key: name for out_key in nand.outputs.keys()}
    )

    return nand_ports

def _connect_inputs(circuit: Circuit, circuit_ports: CircuitPorts, components_ports: ComponentsPorts, graph: pydot.Graph):
    for circuit_input_name, input_wire in circuit.inputs.items():
        for component_name, component in circuit.components.items():
            matching_inputs = (
                input_name
                for input_name, wire in component.inputs.items()
                if wire.id == input_wire.id
            )
            
            for component_input_name in matching_inputs:
                source_node = circuit_ports[circuit_input_name]
                target_node = components_ports[component_name][component_input_name]
                graph.add_edge(pydot.Edge(source_node, target_node))

def _connect_outputs(circuit: Circuit, circuit_ports: CircuitPorts, components_ports: ComponentsPorts, graph: pydot.Graph):
    for circuit_output_name, output_wire in circuit.outputs.items():
        for component_name, component in circuit.components.items():
            matching_outputs = (
                output_name
                for output_name, wire in component.outputs.items()
                if wire.id == output_wire.id
            )
            
            for component_output_name in matching_outputs:
                source_node = components_ports[component_name][component_output_name]
                target_node = circuit_ports[circuit_output_name]

                graph.add_edge(
                    pydot.Edge(source_node, target_node)
                )

def _connect_components(circuit: Circuit, circuit_ports: CircuitPorts, components_ports: ComponentsPorts, graph: pydot.Graph):
    for source_name, source in circuit.components.items():
        for target_name, target in circuit.components.items():
            if source_name == target_name:
                continue

            for source_output_name, source_output_wire in source.outputs.items():
                # Find all target inputs with matching wire id in the destination component.
                matching_inputs = (
                    target_input_name
                    for target_input_name, target_input_wire in target.inputs.items() 
                    if target_input_wire.id == source_output_wire.id
                )

                for target_input_name in matching_inputs:
                    source_node = components_ports[source_name][source_output_name]
                    target_node = components_ports[target_name][target_input_name]
                    graph.add_edge(pydot.Edge(source_node, target_node))

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
