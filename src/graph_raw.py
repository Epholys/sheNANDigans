from typing import List, Tuple
import pydot
from circuit import (
    Circuit,
    CircuitDict,
    PortWireDict,
)
from decoding import CircuitDecoder
from encoding import CircuitEncoder
from schematics import SchematicsBuilder, get_schematic_idx


def generate_circuit_graph(
    circuit: Circuit, filename: str, format: str = "png"
) -> pydot.Graph:
    """ """
    # Create the main graph
    graph = pydot.Dot(
        f"Circuit_{circuit.identifier}",
        graph_type="digraph",
        rankdir="LR",
        label=circuit.identifier,
    )

    # Create the circuit representation directly (not as a subgraph)
    _build_circuit_graph(graph, circuit, {}, "", True)

    # If filename is provided, save the graph
    output_file = f"{filename}.{format}"
    graph.write(output_file, format=format)
    print(f"Graph saved to {output_file}")

    return graph


type Nodes = dict[int, Tuple[str | None, str | None]]
type InputNodes = Nodes
type OutputNodes = Nodes
type PortNodes = Tuple[InputNodes, OutputNodes]


def _build_circuit_graph(
    graph: pydot.Graph,
    circuit: Circuit,
    parent_nodes: PortNodes,
    prefix: str,
    is_main_graph: bool,
) -> PortNodes:
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

    # Add ports nodes
    nodes = parent_nodes
    if is_main_graph:
        inputs_nodes: InputNodes = _add_ports_nodes(
            circuit.inputs, graph, f"{prefix}_in", "#aaffaa", True
        )
        outputs_nodes: OutputNodes = _add_ports_nodes(
            circuit.outputs, graph, f"{prefix}_out", "#ffaaaa", False
        )
        nodes: PortNodes = (inputs_nodes, outputs_nodes)
        print(f"main graph nodes = {nodes}")


    # A mapping between all the components and their ports
    components_nodes: List[PortNodes] = _build_components_graph(circuit, nodes, graph, prefix)

    print(f"component nodes : {components_nodes}")

    nodes = _collapse_ports(nodes, components_nodes, graph)

    

    if is_main_graph:
        (input_nodes, output_nodes) = nodes
        for input in input_nodes.values():
            if input[0] and input[1]:
                graph.add_edge(pydot.Edge(input[0], input[1]))

        for output in output_nodes.values():
            if output[0] and output[1]:
                graph.add_edge(pydot.Edge(output[0], output[1]))

    return nodes


def _add_ports_nodes(
    ports: PortWireDict, graph: pydot.Graph, prefix: str, color: str, is_input: bool
) -> Nodes:
    wires: Nodes = {}

    for port, wire in ports.items():
        node_id = f"{prefix}_{port}"

        if is_input:
            wires[wire.id] = (node_id, None)
        else:
            wires[wire.id] = (None, node_id)

        graph.add_node(
            pydot.Node(
                node_id,
                label=f"{port}",
                shape="circle",
                style="filled",
                fillcolor=color,
            )
        )

    return wires


def _build_components_graph(
    circuit: Circuit,
    circuit_nodes: PortNodes,
    graph: pydot.Graph,
    prefix: str,
) -> List[PortNodes]:
    nodes: List[PortNodes] = []

    if len(circuit.components) == 0:
        # We are at the nand level
        nodes = _build_nand_circuit(circuit, graph, f"{prefix}_nand")
        print(f"nand nodes : {nodes}")

    for component_name, component in circuit.components.items():
        component_prefix = f"{prefix}_comp_{component_name}"

        nodes.append(_build_circuit_graph(
            graph, component, circuit_nodes, component_prefix, False
        ))


    return nodes


def _build_nand_circuit(nand: Circuit, graph: pydot.Graph, name: str) -> List[PortNodes]:
    _add_nand_node(graph, name)

    inputs_nodes: InputNodes = {}
    inputs = list(nand.inputs.values())
    assert len(inputs) == 2
    a = inputs[0]
    inputs_nodes[a.id] = (None, name)
    b = inputs[1]
    inputs_nodes[b.id] = (None, name)

    output_node: OutputNodes = {}
    output = list(nand.outputs.values())
    assert len(output) == 1
    out = output[0]
    output_node[out.id] = (name, None)

    return [(inputs_nodes, output_node)]


def _add_nand_node(graph: pydot.Graph, name: str):
    graph.add_node(
        pydot.Node(
            name,
            label="NAND",
            shape="box",
            style="filled",
            fillcolor="#ccccff",
        )
    )


def _collapse_ports(circuit_nodes: PortNodes, components_nodes: List[PortNodes], graph: pydot.Graph) -> PortNodes:
    circuit_inputs, circuit_outputs = circuit_nodes
    
    inputs_nodes : InputNodes = {}
    for circuit_wire, circuit_input in circuit_inputs.items():
        for component_nodes in components_nodes:
            (component_inputs, _) = component_nodes
            for component_wire, component_input in component_inputs.items():
                if circuit_wire == component_wire:
                    inputs_nodes[circuit_wire] = (circuit_input[0], component_input[1])                

    outputs_nodes : OutputNodes = {}
    for circuit_wire, circuit_output in circuit_outputs.items():
        for component_nodes in components_nodes:
            (_, component_outputs) = component_nodes
            for component_wire, component_output in component_outputs.items():
                if circuit_wire == component_wire:
                    outputs_nodes[circuit_wire] = (component_output[0], circuit_output[1])

    print(f"Starting connecting components : component nodes : {components_nodes}")

    for source_nodes in components_nodes:
        for target_nodes in components_nodes:
            if source_nodes == target_nodes:
                continue

            print(f"source_nodes = {source_nodes}\ntarget_nodes = {target_nodes}")

            (_, source_outputs) = source_nodes
            for source_wire, source_node in source_outputs.items():
                (target_inputs, _) = target_nodes
                for target_wire, target_node in target_inputs.items():
                    if source_wire == target_wire and source_node[0] and target_node[1]:
                        graph.add_edge(
                            pydot.Edge(source_node[0], target_node[1])
                        )

    return (inputs_nodes, outputs_nodes)

def visualize_schematic(
    circuit_idx: int,
    schematics: CircuitDict,
    filename: str,
    format: str = "png",
) -> pydot.Graph:
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

    visualize_schematic(2, reference, "compact", "svg")
    # visualize_schematic(8, round_trip_1, "2bitsadder_roundtrip_1_better_nand")
    # visualize_schematic(8, round_trip_2, "2bitsadder_roundtrip_2_better_nand")
