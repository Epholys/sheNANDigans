import pydot
from circuit import (
    Circuit,
    CircuitDict,
    CircuitKey,
    PortWireDict,
)
from schematics import SchematicsBuilder, get_schematic_idx


class GraphOptions:
    def __init__(self, is_compact: bool, is_aligned: bool):
        self.is_compact = is_compact
        self.is_aligned = is_aligned


def generate_circuit_graph(
    circuit: Circuit, options: GraphOptions, filename: str, format: str = "png"
) -> pydot.Graph:
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
        f"Circuit_{circuit.identifier}",
        graph_type="digraph",
        rankdir="LR",
        label=circuit.identifier,
    )

    # Create the circuit representation directly (not as a subgraph)
    _build_circuit_graph(graph, circuit, "", options, True)

    # If filename is provided, save the graph
    output_file = f"{filename}.{format}"
    graph.write(output_file, format=format)
    print(f"Graph saved to {output_file}")

    return graph


type CircuitPorts = dict[CircuitKey, str]
type ComponentsPorts = dict[CircuitKey, CircuitPorts]


def _build_circuit_graph(
    parent_graph: pydot.Graph,
    circuit: Circuit,
    prefix: str,
    options: GraphOptions,
    is_main_graph: bool = False,
) -> CircuitPorts:
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

    if is_main_graph:
        graph = parent_graph
    else:
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
    if options.is_aligned:
        circuit_ports.update(
            _add_ports_nodes(circuit.inputs, graph, f"{prefix}_in", "#aaffaa", "min")
        )
        circuit_ports.update(
            _add_ports_nodes(circuit.outputs, graph, f"{prefix}_out", "#ffaaaa", "max")
        )
    else:
        circuit_ports.update(
            _add_ports_nodes(circuit.inputs, graph, f"{prefix}_in", "#aaffaa")
        )
        circuit_ports.update(
            _add_ports_nodes(circuit.outputs, graph, f"{prefix}_out", "#ffaaaa")
        )

    # A mapping between all the components and their ports
    components_ports: ComponentsPorts = _build_components_graph(
        circuit.components, circuit_ports, graph, prefix, options
    )

    # Create connections between circuit inputs and component inputs.
    # For each input in the circuit, search in all components the corresponding input wire.
    _connect_inputs(circuit, circuit_ports, components_ports, graph)

    # Connect component outputs to circuit outputs.
    # For each output in the circuit, search in all components the corresponding output wire.
    _connect_outputs(circuit, circuit_ports, components_ports, graph)

    # Connect component outputs to other component inputs.
    # For each components' output, search in all components the corresponding input wire.
    _connect_components(circuit, components_ports, graph)

    # Add the subgraph to the parent graph if this is not the main circuit
    if not is_main_graph:
        parent_graph.add_subgraph(graph)

    return circuit_ports


def _add_ports_nodes(
    ports: PortWireDict,
    graph: pydot.Graph,
    prefix: str,
    color: str,
    rank: str | None = None,
) -> CircuitPorts:
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

    if rank:
        subgraph_name = f"aligned_{rank}_{prefix}"
        subgraph = pydot.Subgraph(subgraph_name, rank=rank)
        for node_id in port_node_ids.values():
            subgraph.add_node(pydot.Node(node_id))
        graph.add_subgraph(subgraph)

    return port_node_ids


def _build_components_graph(
    components: CircuitDict,
    circuit_ports: CircuitPorts,
    graph: pydot.Graph,
    prefix: str,
    options: GraphOptions,
) -> ComponentsPorts:
    component_ports: ComponentsPorts = {}

    if len(components) == 0 and not options.is_compact:
        # We are at the nand level
        _build_nand_circuit(circuit_ports, graph, prefix)

    for component_name, component in components.items():
        component_prefix = f"{prefix}_comp_{component_name}"

        if component.identifier == 0 and options.is_compact:
            # If the component is a NAND gate and we want a compact graph, let's do a shortcut:
            # We do not build the NAND graph but just the NAND box with in/out directly on it
            component_ports[component_name] = _build_nand_component(
                component, graph, component_prefix
            )
        else:
            # For non-NAND components, process them recursively.
            component_ports[component_name] = _build_circuit_graph(
                graph, component, component_prefix, options
            )

    return component_ports


def _build_nand_component(nand: Circuit, graph: pydot.Graph, name: str) -> CircuitPorts:
    _add_nand_node(graph, name)

    # As it is a compact graph, the inputs and outputs of NAND gates are "collapsed" into the gate itself
    nand_ports: CircuitPorts = {in_key: name for in_key in nand.inputs.keys()}
    nand_ports.update({out_key: name for out_key in nand.outputs.keys()})

    return nand_ports


def _build_nand_circuit(circuit_ports: CircuitPorts, graph: pydot.Graph, name: str):
    _add_nand_node(graph, name)

    ports = list(circuit_ports.values())
    a = ports[0]
    b = ports[1]
    out = ports[2]
    graph.add_edge(pydot.Edge(a, name))
    graph.add_edge(pydot.Edge(b, name))
    graph.add_edge(pydot.Edge(name, out))


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


def _connect_inputs(
    circuit: Circuit,
    circuit_ports: CircuitPorts,
    components_ports: ComponentsPorts,
    graph: pydot.Graph,
):
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


def _connect_outputs(
    circuit: Circuit,
    circuit_ports: CircuitPorts,
    components_ports: ComponentsPorts,
    graph: pydot.Graph,
):
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

                graph.add_edge(pydot.Edge(source_node, target_node))


def _connect_components(
    circuit: Circuit,
    components_ports: ComponentsPorts,
    graph: pydot.Graph,
):
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


def visualize_schematic(
    circuit_idx: int,
    schematics: CircuitDict,
    options: GraphOptions,
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
    return generate_circuit_graph(circuit, options, filename, format)


# Example usage
if __name__ == "__main__":
    import os

    # Set Graphviz path if needed
    os.environ["PATH"] += os.pathsep + "C:/Program Files/Graphviz/bin"

    # Create schematics library
    schematics_builder = SchematicsBuilder()
    schematics_builder.build_circuits()
    reference = schematics_builder.schematics

    # encoder = CircuitEncoder(reference.copy())
    # encoded = encoder.encode()
    # decoder = CircuitDecoder(encoded.copy())
    # round_trip_1 = decoder.decode()

    # encoder = CircuitEncoder(round_trip_1.copy())
    # encoded = encoder.encode()
    # decoder = CircuitDecoder(encoded.copy())
    # round_trip_2 = decoder.decode()

    # Visualize different circuits
    for idx in [10]:  # Visualize first 9 circuits
        try:
            visualize_schematic(
                idx,
                reference,
                GraphOptions(is_compact=True, is_aligned=True),
                f"circuit_{idx}",
                "svg",
            )
        except Exception as e:
            print(f"Error visualizing circuit {idx}: {e}")
