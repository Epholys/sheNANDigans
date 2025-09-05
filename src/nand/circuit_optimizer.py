import matplotlib.pyplot as plt
from enum import Enum
from dataclasses import dataclass
from typing import List

import networkx as nx

from nand.circuit import Circuit


class _NodeKind(Enum):
    """The different kind of nodes.

    CIRCUIT_INPUT represents the circuit inputs.
    CIRCUIT_OUTPUT represents the circuit outputs.
    COMPONENT represents a component.
    """

    CIRCUIT_INPUT = "IN"
    CIRCUIT_OUTPUT = "OUT"
    COMPONENT = "C"


@dataclass(frozen=True)
class _Node:
    """A Node fort a nx graph.

    kind: Indicate if the node represents
        - all the circuit inputs,
        - all the circuit outputs,
        - a single component.
    idx: The index of a component, or None if the node doesn't represent one.
    """

    kind: _NodeKind
    idx: int | None

    def __str__(self):
        id_ = str(self.idx) if self.idx is not None else ""
        return f"{self.kind.value} {id_}"


def _draw_sorted_graph(graph: nx.Graph, name: str):
    """Debug visualization."""
    for layer, nodes in enumerate(nx.topological_generations(graph)):
        # `multipartite_layout` expects the layer as a node attribute, so add the
        # numeric layer value as a node attribute
        for node in nodes:
            graph.nodes[node]["layer"] = layer

    # Compute the multipartite_layout using the "layer" node attribute
    pos = nx.multipartite_layout(graph, subset_key="layer")

    fig, ax = plt.subplots()
    nx.draw_networkx(graph, pos=pos, ax=ax)
    ax.set_title(name)
    fig.tight_layout()
    plt.show()


def optimize(circuit: Circuit):
    """Optimizes a circuit for efficient simulation by reordering its components.
    This optimization allows to simulate each component sequentially in a single pass.

    This function performs two main tasks:
    1. Recursively optimizes all sub-components of the circuit
    2. Reorders components based on their dependencies using topological sorting

    The reordering algorithm itself is done in several steps:

    The first step is to map the wire connections into a graph structure:
    - Connections between circuit inputs and relevant component inputs
    - Connections between circuit outputs and relevant component outputs
    - Connection between relevant component outputs and other component inputs

    The second step is to do a topological sort of the graph, to untangle the
    dependency.

    The third and last step to the translate this sorted graph back to the component
    structure, to have the final order of components optimized for simulation.

    Args:
        circuit: The circuit to optimize

    Note:
        The optimization is performed in-place, modifying the original circuit.

    TODO optimize optimize():
        Very inefficient: the circuits are built on top of the others, smaller ones.
        So the recursive optimization do the same work again and again for each
        identical circuit. Memoization would be a no-brainer.
    """
    # Base case: empty circuit requires no optimization
    if not circuit.components or circuit.identifier == 0:
        return

    # First recursively optimize all sub-components
    for component in circuit.components.values():
        optimize(component)

    # Build a directed graph representing component dependencies
    graph = build_dependency_graph(circuit)

    # Reorder the components to respect a topological order.
    reorder_components(circuit, graph)


def build_dependency_graph(circuit: Circuit) -> nx.DiGraph:
    """Build the wires dependency graph.

    The nodes of the graphs are either the circuit inputs, circuit outputs,
    or a components. The circuit ports are "virtual" component, the first node and
    the last node.

    The edges are the wires of the circuit, and as such encode the dependencies between
    components.

    TODO: Optimize: each component inputs and outputs are read too many times, in nested
          loops. Building a/some data structure/s containing all of them and
          removing them as soon as the edge is built would be better.
    """
    graph = nx.DiGraph()

    _add_input_edges(circuit, graph)
    _add_outputs_edges(circuit, graph)
    _add_components_edges(circuit, graph)

    return graph


def _add_input_edges(circuit: Circuit, graph: nx.DiGraph):
    """Add the edges from the circuit inputs."""
    for circuit_input in circuit.inputs.values():
        for idx, component in enumerate(circuit.components.values()):
            for component_input in component.inputs.values():
                if circuit_input.id == component_input.id:
                    graph.add_edge(
                        _Node(_NodeKind.CIRCUIT_INPUT, None),
                        _Node(_NodeKind.COMPONENT, idx),
                    )


def _add_outputs_edges(circuit: Circuit, graph: nx.DiGraph):
    """Add the edges to the circuit outputs."""
    for circuit_output in circuit.outputs.values():
        for idx, component in enumerate(circuit.components.values()):
            for component_output in component.outputs.values():
                if circuit_output.id == component_output.id:
                    graph.add_edge(
                        _Node(_NodeKind.COMPONENT, idx),
                        _Node(_NodeKind.CIRCUIT_OUTPUT, None),
                    )


def _add_components_edges(circuit: Circuit, graph: nx.DiGraph):
    """Add the edges between components ports."""
    components = list(circuit.components.values())
    for i1, c1 in enumerate(components):
        for i2, c2 in enumerate(components):
            if i1 == i2:
                continue
            for output_ in c1.outputs.values():
                for input_ in c2.inputs.values():
                    if output_.id == input_.id:
                        graph.add_edge(
                            _Node(_NodeKind.COMPONENT, i1),
                            _Node(_NodeKind.COMPONENT, i2),
                        )


def reorder_components(circuit: Circuit, graph: nx.Graph):
    """Reorder the components of the circuit to respect a topological order.

    Doing so, a simple iteration over the components is enough to simulate it: no wire
    would be undefined.
    """
    # The index of the component is saved in the node: it's the way to track it.
    #
    # For example, if the circuit has 3 components and the sorted nodes has
    # these indices: [1, 0, 2], it means that the first two components must be swapped
    # to respect the topological order.
    sorted_nodes: List[_Node] = list(nx.topological_sort(graph))

    # Extract the components index, removing the virtual component of circuit
    # inputs and outputs.
    sorted_component_idx = [node.idx for node in sorted_nodes if node.idx is not None]

    # Get the current component, in the original order.
    components = list(circuit.components.items())

    # Reorder the components.
    circuit.components = {
        components[idx][0]: components[idx][1] for idx in sorted_component_idx
    }
