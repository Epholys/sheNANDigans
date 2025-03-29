from enum import Enum
from dataclasses import dataclass
from itertools import groupby
from typing import List, Tuple, Dict, Set, Optional

import networkx as nx

from circuit import Circuit, CircuitDict, CircuitKey, Key, Wire


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
    graph, component_nodes = build_dependency_graph(circuit)

    # Topologically sort components and reorder them
    reorder_components(circuit, graph, component_nodes)


def build_dependency_graph(circuit: Circuit) -> Tuple[nx.DiGraph, Dict[int, GraphNode]]:
    """Builds a directed graph representing the dependencies between circuit components.

    Args:
        circuit: The circuit whose components to analyze

    Returns:
        A tuple containing:
        - A directed graph where edges represent connections between components
        - A dictionary mapping component indices to their input nodes in the graph
    """
    graph = nx.DiGraph()
    components = list(circuit.components.values())

    # Create nodes for all circuit and component ports
    circuit_input_nodes: List[GraphNode] = []
    circuit_output_nodes: List[GraphNode] = []
    component_input_nodes: List[GraphNode] = []
    component_output_nodes: List[GraphNode] = []

    # Map wire IDs to nodes for quick lookup
    wire_to_nodes: Dict[int, List[GraphNode]] = {}

    # Create nodes for circuit inputs
    for port_key, wire in circuit.inputs.items():
        node = GraphNode(
            node_type=NodeType.CIRCUIT_INPUT,
            component_id=None,
            component_idx=None,
            port_key=port_key,
            wire_id=wire.id,
        )
        circuit_input_nodes.append(node)
        wire_to_nodes.setdefault(wire.id, []).append(node)
        graph.add_node(node)

    # Create nodes for circuit outputs
    for port_key, wire in circuit.outputs.items():
        node = GraphNode(
            node_type=NodeType.CIRCUIT_OUTPUT,
            component_id=None,
            component_idx=None,
            port_key=port_key,
            wire_id=wire.id,
        )
        circuit_output_nodes.append(node)
        wire_to_nodes.setdefault(wire.id, []).append(node)
        graph.add_node(node)

    # Create nodes for component inputs and outputs
    for idx, component in enumerate(components):
        for port_key, wire in component.inputs.items():
            node = GraphNode(
                node_type=NodeType.COMPONENT_INPUT,
                component_id=component.identifier,
                component_idx=idx,
                port_key=port_key,
                wire_id=wire.id,
            )
            component_input_nodes.append(node)
            wire_to_nodes.setdefault(wire.id, []).append(node)
            graph.add_node(node)

        for port_key, wire in component.outputs.items():
            node = GraphNode(
                node_type=NodeType.COMPONENT_OUTPUT,
                component_id=component.identifier,
                component_idx=idx,
                port_key=port_key,
                wire_id=wire.id,
            )
            component_output_nodes.append(node)
            wire_to_nodes.setdefault(wire.id, []).append(node)
            graph.add_node(node)

    # Add edges based on wire connections
    for nodes in wire_to_nodes.values():
        source_nodes = [
            node
            for node in nodes
            if node.node_type in (NodeType.CIRCUIT_INPUT, NodeType.COMPONENT_OUTPUT)
        ]

        target_nodes = [
            node
            for node in nodes
            if node.node_type in (NodeType.COMPONENT_INPUT, NodeType.CIRCUIT_OUTPUT)
        ]

        for source in source_nodes:
            for target in target_nodes:
                graph.add_edge(source, target)

    # Create a mapping of component indices to their input nodes
    component_nodes = {
        node.component_idx: node
        for node in component_input_nodes
        if node.component_idx is not None
    }

    return graph, component_nodes


def reorder_components(
    circuit: Circuit, graph: nx.DiGraph, component_nodes: Dict[int, GraphNode]
) -> None:
    """Reorders the components of a circuit based on a topological sort of the dependency graph.

    Args:
        circuit: The circuit whose components to reorder
        graph: The directed graph of component dependencies
        component_nodes: Mapping of component indices to their input nodes
    """
    # Get topologically sorted nodes
    sorted_nodes = list(nx.topological_sort(graph))

    # Extract component input nodes in sorted order
    sorted_component_nodes = [
        node for node in sorted_nodes if node.node_type == NodeType.COMPONENT_INPUT
    ]

    # Get unique component indices while preserving order
    seen_indices: Set[int] = set()
    ordered_indices: List[int] = []

    for node in sorted_component_nodes:
        if node.component_idx is not None and node.component_idx not in seen_indices:
            ordered_indices.append(node.component_idx)
            seen_indices.add(node.component_idx)

    # Create a new ordered component dictionary
    components_list = list(circuit.components.items())
    ordered_components: CircuitDict = {}

    for idx in ordered_indices:
        if idx < len(components_list):
            key, component = components_list[idx]
            ordered_components[key] = component

    # Update the circuit with the ordered components
    circuit.components = ordered_components
