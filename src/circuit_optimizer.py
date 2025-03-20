from itertools import groupby
from typing import List, Tuple

import networkx

from src.circuit import Circuit, CircuitDict, CircuitKey, Wire


def optimize(circuit: Circuit):
    if len(circuit.components) == 0:
        return

    for component in circuit.components.values():
        optimize(component)

    components: List[Circuit] = [component for component in circuit.components.values()]

    raw_components_inputs: List[Tuple[str, List[Wire]]] = [
        (f"comp_in_{component.identifier}_{idx}", list(component.inputs.values()))
        for idx, component in enumerate(components)
    ]

    components_inputs: List[Tuple[str, Wire]] = [
        (key, wire) for key, wires in raw_components_inputs for wire in wires
    ]

    raw_components_outputs: List[Tuple[str, List[Wire]]] = [
        (f"comp_out_{component.identifier}_{idx}", list(component.outputs.values()))
        for idx, component in enumerate(components)
    ]

    components_outputs: List[Tuple[str, Wire]] = [
        (key, wire) for key, wires in raw_components_outputs for wire in wires
    ]

    inputs: List[Tuple[str, Wire]] = list(
        (f"ct_in_{input[0]}_{idx}", input[1])
        for idx, input in enumerate(circuit.inputs.items())
    )
    outputs: List[Tuple[str, Wire]] = list(
        (f"ct_out_{output[0]}_{idx}", output[1])
        for idx, output in enumerate(circuit.outputs.items())
    )

    for input in inputs:
        for component_input in components_inputs:
            if input[1].id == component_input[1].id:
                circuit.graph.add_edge(input[0], component_input[0])

    for output in outputs:
        for component_output in components_outputs:
            if output[1].id == component_output[1].id:
                circuit.graph.add_edge(component_output[0], output[0])

    for component_output in components_outputs:
        for component_input in components_inputs:
            if component_input[1] == component_output[1]:
                circuit.graph.add_edge(component_output[0], component_input[0])

    sorted = list(networkx.topological_sort(circuit.graph))
    components_named_duplicate = [key for key, _ in components_inputs]
    components_named = [key for key, _ in groupby(components_named_duplicate)]
    sorted_only_components = [
        comp_name for comp_name in sorted if comp_name in components_named_duplicate
    ]

    indices_order: List[int] = []
    for node in sorted_only_components:
        indices_order.append(components_named.index(node))
    components_list: List[Tuple[CircuitKey, "Circuit"]] = list(
        circuit.components.items()
    )
    ordered_components: CircuitDict = {}
    for index in indices_order:
        (key, component) = components_list[index]
        ordered_components[key] = component
    circuit.components = ordered_components
