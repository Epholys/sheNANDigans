from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Set, Optional

import networkx as nx

from circuit import Circuit, CircuitDict, CircuitKey, Key, PortWireDict


class NodeType(Enum):
    """Enumeration of possible node types in the circuit dependency graph."""

    CIRCUIT_INPUT = "circuit_input"
    CIRCUIT_OUTPUT = "circuit_output"
    COMPONENT_INPUT = "component_input"
    COMPONENT_OUTPUT = "component_output"


@dataclass(frozen=True)
class GraphNode:
    """A node in the circuit dependency graph.

    Attributes:
        node_type: The type of node (input/output of circuit/component)
        component_id: The ID of the component (None for circuit nodes)
        component_idx: The index of the component in the circuit's component list
        (None for circuit nodes)
        port_key: The key of the input/output port
        wire_id: The ID of the wire connected to this node
    """

    node_type: NodeType
    component_id: Optional[CircuitKey]
    component_idx: Optional[int]
    port_key: Key
    wire_id: int

    def __str__(self) -> str:
        """String representation for debugging."""
        if self.node_type in (NodeType.CIRCUIT_INPUT, NodeType.CIRCUIT_OUTPUT):
            return f"{self.node_type.value}:{self.port_key}"
        else:
            return (
                f"{self.node_type.value}:{self.component_id}:"
                f"{self.component_idx}:{self.port_key}"
            )


def optimize(circuit: Circuit) -> None:
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
    graph = build_dependency_graph(circuit)

    # Topologically sort components and reorder them
    reorder_components(circuit, graph)


def build_dependency_graph(
    circuit: Circuit,
) -> nx.DiGraph:
    """Builds a directed graph representing the dependencies between circuit components.

    Args:
        circuit: The circuit whose components to analyze

    Returns:
        A directed graph where edges represent connections between components
    """
    graph = nx.DiGraph()
    components = list(circuit.components.values())

    # Create nodes for all circuit and component ports using helper functions
    circuit_input_nodes = create_circuit_port_nodes(
        circuit.inputs, NodeType.CIRCUIT_INPUT
    )
    circuit_output_nodes = create_circuit_port_nodes(
        circuit.outputs, NodeType.CIRCUIT_OUTPUT
    )
    component_input_nodes = create_component_port_nodes(
        components, NodeType.COMPONENT_INPUT
    )
    component_output_nodes = create_component_port_nodes(
        components, NodeType.COMPONENT_OUTPUT
    )

    # Add all nodes to the graph
    all_nodes = (
        circuit_input_nodes
        + circuit_output_nodes
        + component_input_nodes
        + component_output_nodes
    )
    for node in all_nodes:
        graph.add_node(node)

    # Create a wire-to-nodes mapping for efficient edge creation
    wire_to_nodes: Dict[int, List[GraphNode]] = {}
    for node in all_nodes:
        wire_to_nodes.setdefault(node.wire_id, []).append(node)

    # Add edges based on wire connections
    for wiring_nodes in wire_to_nodes.values():
        source_nodes = [
            node
            for node in wiring_nodes
            if node.node_type in (NodeType.CIRCUIT_INPUT, NodeType.COMPONENT_OUTPUT)
        ]

        target_nodes = [
            node
            for node in wiring_nodes
            if node.node_type in (NodeType.COMPONENT_INPUT, NodeType.CIRCUIT_OUTPUT)
        ]

        for source in source_nodes:
            for target in target_nodes:
                graph.add_edge(source, target)

    return graph


def reorder_components(circuit: Circuit, graph: nx.DiGraph) -> None:
    """Reorders the components of a circuit based on a topological sort of the dependency graph.

    Args:
        circuit: The circuit whose components to reorder
        graph: The directed graph of component dependencies
        node_info: Dictionary containing node lists by type
    """
    # Get topologically sorted nodes
    sorted_nodes = list(nx.topological_sort(graph))

    # Extract component input nodes in sorted order
    sorted_component_input_nodes: List[GraphNode] = [
        node for node in sorted_nodes if node.node_type == NodeType.COMPONENT_INPUT
    ]

    # Get unique component indices while preserving order
    seen_indices: Set[int] = set()
    ordered_indices: List[int] = []

    for node in sorted_component_input_nodes:
        if node.component_idx is None:
            raise ValueError(
                f"The node {node} should have a component index "
                f"(as it must be a component input node)."
            )
        if node.component_idx not in seen_indices:
            ordered_indices.append(node.component_idx)
            seen_indices.add(node.component_idx)

    # Create a new ordered component dictionary
    components_list = list(circuit.components.items())
    ordered_components: CircuitDict = {}

    for idx in ordered_indices:
        if idx >= len(components_list):
            raise ValueError(
                f"The index {idx} of 'ordered_indices' is out of bounds "
                f"of the components list. It means something went very wrong "
                f"with the topological sort."
            )
        if idx < len(components_list):
            key, component = components_list[idx]
            ordered_components[key] = component

    # Update the circuit with the ordered components
    circuit.components = ordered_components


def create_circuit_port_nodes(
    ports: PortWireDict, node_type: NodeType
) -> List[GraphNode]:
    """Creates graph nodes for all circuit input ports.

    Args:
        circuit: The circuit to create nodes for

    Returns:
        A list of graph nodes representing circuit inputs
    """
    nodes = []
    for port_key, wire in ports.items():
        node = GraphNode(
            node_type=node_type,
            component_id=None,
            component_idx=None,
            port_key=port_key,
            wire_id=wire.id,
        )
        nodes.append(node)
    return nodes


def create_component_port_nodes(
    components: List[Circuit], node_type: NodeType
) -> List[GraphNode]:
    """Creates graph nodes for all component input ports.

    Args:
        components: The list of components to create nodes for

    Returns:
        A list of graph nodes representing component inputs
    """

    def get_ports(component):
        return (
            component.inputs
            if node_type == NodeType.COMPONENT_INPUT
            else component.outputs
        )

    nodes = []
    for idx, component in enumerate(components):
        for port_key, wire in get_ports(component).items():
            node = GraphNode(
                node_type=node_type,
                component_id=component.identifier,
                component_idx=idx,
                port_key=port_key,
                wire_id=wire.id,
            )
            nodes.append(node)
    return nodes
