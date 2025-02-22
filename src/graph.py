from calendar import c
import os

import pydot
import schematics
from circuit import Circuit, CircuitKey

def comp_key(component: Circuit, idx: CircuitKey, suffix: str = '') -> str:
    return f"COMPONENT_{component.identifier}_{idx}{suffix}"

def comp_label(component: Circuit) -> str:
    return f"COMPONENT_{component.identifier}"

def in_val(idx :CircuitKey) -> str:
    return f"IN_{idx}"

def out_val(idx :CircuitKey) -> str:
    return f"OUT_{idx}"

# def find_ins(circuit: Circuit, )

def build_graph(circuit: Circuit, recursive: bool = False, suffix: str = '') -> pydot.Dot:
    graph = pydot.Dot(f"{circuit.identifier}", graph_type='digraph')

    for (idx, component) in enumerate(circuit.components.values()):
        graph.add_node(pydot.Node(f"{comp_key(component, idx)}", shape='box', label=f"{comp_label(component)}"))

    for (idx, wire) in circuit.inputs.items():
        graph.add_node(pydot.Node(f"{in_val(idx)}", shape='circle', label=f"{in_val(idx)}"))
        for (comp_idx, component) in enumerate(circuit.components.values()):        
            in_idxs = [in_idx for in_idx, in_wire in enumerate(component.inputs.values()) if in_wire.id == wire.id]
            for in_idx in in_idxs:
                if not recursive:
                    graph.add_edge(pydot.Edge(f"{in_val(idx)}", f"{comp_key(component, comp_idx)}"))

    for (idx, wire) in circuit.outputs.items():
        graph.add_node(pydot.Node(f"{out_val(idx)}", shape='circle', label=f"{out_val(idx)}"))
        for (comp_idx, component) in enumerate(circuit.components.values()):        
            out_idxs = [out_idx for out_idx, out_wire in enumerate(component.outputs.values()) if out_wire.id == wire.id]
            for out_idx in out_idxs:
                if not recursive:
                    graph.add_edge(pydot.Edge(f"{comp_key(component, comp_idx)}", f"{out_val(idx)}"))

    for (idx, component) in enumerate(circuit.components.values()):
        for (out_idx, out_wire) in component.outputs.items():
            for (comp_idx, other_component) in enumerate(circuit.components.values()):
                in_idxs = [in_idx for in_idx, in_wire in enumerate(other_component.inputs.values()) if in_wire.id == out_wire.id]
                for in_idx in in_idxs:
                    if not recursive:
                        graph.add_edge(pydot.Edge(f"{comp_key(component, idx)}", f"{comp_key(other_component, comp_idx)}"))

    return graph


schematics_builder = schematics.SchematicsBuilder()
schematics_builder.build_circuits()
circuits = schematics_builder.schematics
gate = schematics.get_schematic(5, circuits)
graph = build_graph(gate)
#  write(self, path, prog=None, format="raw", encoding=None):
os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin'
graph.write(path="xor_graph.png", format="png") # type: ignore


    