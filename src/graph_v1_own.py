import pydot
from circuit import Circuit, CircuitKey

def generate_circuit_graph(circuit: Circuit, filename: str = None, format: str = "png"):
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
    main_graph = pydot.Dot(f"Circuit_{circuit.identifier}", graph_type='digraph', rankdir="LR")
    
    # Track wire connections to avoid duplicates
    wire_connections = set()
    
    # Create the circuit representation directly (not as a subgraph)
    _build_circuit_graph(main_graph, circuit, "", wire_connections, is_main_circuit=True)
    
    # If filename is provided, save the graph
    if filename:
        output_file = f"{filename}.{format}"
        main_graph.write(output_file, format=format)
        print(f"Graph saved to {output_file}")
        
    return main_graph

def _build_circuit_graph(parent_graph, circuit: Circuit, prefix, wire_connections, is_main_circuit=False):
    """
    Recursively build a circuit and its components as nested subgraphs.
    
    Args:
        parent_graph: The parent graph to add this circuit to
        circuit: The circuit to visualize
        prefix: A prefix to make node IDs unique
        wire_connections: Set tracking which wire connections have been processed
        is_main_circuit: Whether this is the main circuit (not wrapped in a cluster)
        
    Returns:
        A dictionary mapping (port_type, port_key) to node_id
    """
    # Create nodes for this level
    port_nodes = {}
    
    # If this is not the main circuit, create a subgraph
    if not is_main_circuit:
        circuit_name = f"cluster_{prefix}_{circuit.identifier}"
        subgraph = pydot.Cluster(
            circuit_name, 
            label=f"Circuit {circuit.identifier}",
            style="rounded,filled",
            fillcolor="#f0f0f0",
            color="#000000"
        )
        graph_to_use = subgraph
    else:
        # For main circuit, use the parent graph directly
        graph_to_use = parent_graph
    
    # Add input nodes
    for in_key, wire in circuit.inputs.items():
        node_id = f"{prefix}_in_{in_key}"
        port_nodes[('in', in_key)] = node_id
        graph_to_use.add_node(pydot.Node(
            node_id,
            label=f"{in_key}",
            shape="circle",
            style="filled",
            fillcolor="#aaffaa"
        ))
    
    # Add output nodes
    for out_key, wire in circuit.outputs.items():
        node_id = f"{prefix}_out_{out_key}"
        port_nodes[('out', out_key)] = node_id
        graph_to_use.add_node(pydot.Node(
            node_id,
            label=f"{out_key}",
            shape="circle",
            style="filled",
            fillcolor="#ffaaaa"
        ))
    
    # Special case for NAND gate (base component)
    if circuit.identifier == 0:
        # Add a node representing the NAND functionality
        nand_node_id = f"{prefix}_nand_gate"
        graph_to_use.add_node(pydot.Node(
            nand_node_id,
            label="NAND",
            shape="box",
            style="filled",
            fillcolor="#ccccff"
        ))
        
        # Connect inputs to the NAND node
        for in_key, wire in circuit.inputs.items():
            parent_graph.add_edge(pydot.Edge(
                port_nodes[('in', in_key)], 
                nand_node_id
            ))
        
        # Connect the NAND node to the output
        for out_key, wire in circuit.outputs.items():
            parent_graph.add_edge(pydot.Edge(
                nand_node_id, 
                port_nodes[('out', out_key)]
            ))
    else:
        # Process all component circuits recursively
        component_ports = {}
        
        # Build all component subgraphs
        for comp_key, component in circuit.components.items():
            comp_prefix = f"{prefix}_comp_{comp_key}"
            component_ports[comp_key] = _build_circuit_graph(
                graph_to_use, component, comp_prefix, wire_connections
            )
            
        # Create direct connections between circuit inputs and component inputs
        for circuit_in_key, wire in circuit.inputs.items():
            wire_id = wire.id
            
            # Connect to all matching component inputs
            for comp_key, component in circuit.components.items():
                for comp_in_key, comp_wire in component.inputs.items():
                    if comp_wire.id == wire_id:
                        # Create a direct connection between circuit input and component input
                        connection = (wire_id, port_nodes[('in', circuit_in_key)], 
                                      component_ports[comp_key][('in', comp_in_key)])
                        if connection not in wire_connections:
                            parent_graph.add_edge(pydot.Edge(
                                port_nodes[('in', circuit_in_key)], 
                                component_ports[comp_key][('in', comp_in_key)]
                            ))
                            wire_connections.add(connection)
        
        # Connect component outputs to circuit outputs
        for circuit_out_key, wire in circuit.outputs.items():
            wire_id = wire.id
            
            # Find which component produces this output
            for comp_key, component in circuit.components.items():
                for comp_out_key, comp_wire in component.outputs.items():
                    if comp_wire.id == wire_id:
                        # Create direct connection between component output and circuit output
                        connection = (wire_id, component_ports[comp_key][('out', comp_out_key)], 
                                      port_nodes[('out', circuit_out_key)])
                        if connection not in wire_connections:
                            parent_graph.add_edge(pydot.Edge(
                                component_ports[comp_key][('out', comp_out_key)], 
                                port_nodes[('out', circuit_out_key)]
                            ))
                            wire_connections.add(connection)
        
        # Connect component outputs to other component inputs
        for src_comp_key, src_component in circuit.components.items():
            for src_out_key, src_wire in src_component.outputs.items():
                src_wire_id = src_wire.id
                
                # Find all components that use this wire as input
                for tgt_comp_key, tgt_component in circuit.components.items():
                    if src_comp_key == tgt_comp_key:
                        continue  # Skip self-connections
                        
                    for tgt_in_key, tgt_wire in tgt_component.inputs.items():
                        if tgt_wire.id == src_wire_id:
                            # Create direct connection between one component's output and another's input
                            connection = (src_wire_id, 
                                          component_ports[src_comp_key][('out', src_out_key)], 
                                          component_ports[tgt_comp_key][('in', tgt_in_key)])
                            if connection not in wire_connections:
                                parent_graph.add_edge(pydot.Edge(
                                    component_ports[src_comp_key][('out', src_out_key)], 
                                    component_ports[tgt_comp_key][('in', tgt_in_key)]
                                ))
                                wire_connections.add(connection)
    
    # Add the subgraph to the parent graph if this is not the main circuit
    if not is_main_circuit:
        parent_graph.add_subgraph(subgraph)
    
    return port_nodes

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
    os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin'
    
    # Create schematics library
    schematics_builder = schematics.SchematicsBuilder()
    schematics_builder.build_circuits()
    
    # Visualize different circuits
    visualize_schematic(0, schematics_builder, "nand_gate_own")
    visualize_schematic(1, schematics_builder, "not_gate_own")
    visualize_schematic(2, schematics_builder, "and_gate_own")
    visualize_schematic(3, schematics_builder, "or_gate_own") 
    visualize_schematic(5, schematics_builder, "xor_gate_own")
    visualize_schematic(6, schematics_builder, "half_adder_own")