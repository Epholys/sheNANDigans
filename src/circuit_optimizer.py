import networkx

from src.circuit import Circuit


def optimize(circuit: Circuit):
    """Optimizes a circuit by recursively optimizing its components and
    reordering them based on topological dependencies.

    Args:
        circuit: The circuit to optimize
    """
    # Base case: empty circuit requires no optimization
    if not circuit.components:
        return

    # First recursively optimize all sub-components
    for component in circuit.components.values():
        optimize(component)

    # Build a directed graph representing component dependencies
    graph = _build_dependency_graph(circuit)

    # Topologically sort components and reorder them
    _reorder_components(circuit, graph)


def _build_dependency_graph(circuit: Circuit) -> networkx.DiGraph:
    """Builds a directed graph representing the dependencies between circuit components.

    Args:
        circuit: The circuit whose components to analyze

    Returns:
        A directed graph where edges represent connections between components
    """
    graph = networkx.DiGraph()
    components = list(circuit.components.values())

    # Map component inputs and outputs to node names in the graph
    component_inputs = []
    component_outputs = []

    for idx, component in enumerate(components):
        input_key = f"comp_in_{component.identifier}_{idx}"
        for wire in component.inputs.values():
            component_inputs.append((input_key, wire))

        output_key = f"comp_out_{component.identifier}_{idx}"
        for wire in component.outputs.values():
            component_outputs.append((output_key, wire))

    # Map circuit inputs and outputs to node names
    circuit_inputs = [
        (f"ct_in_{key}_{idx}", wire)
        for idx, (key, wire) in enumerate(circuit.inputs.items())
    ]

    circuit_outputs = [
        (f"ct_out_{key}_{idx}", wire)
        for idx, (key, wire) in enumerate(circuit.outputs.items())
    ]

    # Add edges from circuit inputs to component inputs
    for circuit_in_key, circuit_in_wire in circuit_inputs:
        for comp_in_key, comp_in_wire in component_inputs:
            if circuit_in_wire.id == comp_in_wire.id:
                graph.add_edge(circuit_in_key, comp_in_key)

    # Add edges from component outputs to circuit outputs
    for comp_out_key, comp_out_wire in component_outputs:
        for circuit_out_key, circuit_out_wire in circuit_outputs:
            if comp_out_wire.id == circuit_out_wire.id:
                graph.add_edge(comp_out_key, circuit_out_key)

    # Add edges between component outputs and inputs
    for comp_out_key, comp_out_wire in component_outputs:
        for comp_in_key, comp_in_wire in component_inputs:
            if comp_out_wire.id == comp_in_wire.id:
                graph.add_edge(comp_out_key, comp_in_key)

    return graph


def _reorder_components(circuit: Circuit, graph: networkx.DiGraph):
    """Reorders the components of a circuit based on a topological sort of the dependency graph.

    Args:
        circuit: The circuit whose components to reorder
        graph: The directed graph of component dependencies
    """
    # Get topologically sorted nodes
    sorted_nodes = list(networkx.topological_sort(graph))

    # Extract component names and remove duplicates while preserving order
    component_names = []
    seen = set()
    for node in sorted_nodes:
        if node.startswith("comp_in_") and node not in seen:
            component_names.append(node)
            seen.add(node)

    # Determine the new order of components
    components_list = list(circuit.components.items())
    ordered_components = {}

    for node in component_names:
        # Extract the index from the node name
        idx = int(node.split("_")[-1])
        key, component = components_list[idx]
        ordered_components[key] = component

    circuit.components = ordered_components
