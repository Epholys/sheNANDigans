from typing import List

from circuit import Circuit, CircuitDict, Wire


class CircuitEncoder:
    def __init__(self, library: CircuitDict):
        self.library = library.copy()
        self.circuits_ids = list(library.keys())
        self.library.popitem(last=False)

    def encode(self) -> List[int]:
        data: List[int] = []
        for circuit in self.library.values():
            data.extend(self.encode_circuit(circuit))
        return data

    def encode_circuit(self, circuit: Circuit) -> List[int]:
        data: List[int] = []
        data.extend(self.encode_header(circuit))
        for component in circuit.components.values():
            data.extend(self.encode_component(component, circuit))
        data.extend(self.encode_outputs(circuit))
        return data

    def encode_header(self, circuit: Circuit) -> List[int]:
        data: List[int] = []
        data.append(len(circuit.components))
        data.append(len(circuit.inputs))
        data.append(len(circuit.outputs))
        return data

    def encode_component(self, component: Circuit, circuit: Circuit) -> List[int]:
        data: List[int] = []
        circuits_input_wires_id = [wire.id for wire in circuit.inputs.values()]

        # Encode component id
        data.append(self.circuits_ids.index(component.identifier))

        # Encode input wires
        length_data = len(data)
        for wire in component.inputs.values():
            if wire.id in circuits_input_wires_id:
                # Provenance
                data.append(0)
                data.append(circuits_input_wires_id.index(wire.id))
            else:
                subcomponents = circuit.components
                data.append(1)
                wiring = self.encode_component_wiring(subcomponents, wire)
                data.extend(wiring)
        if length_data == len(data):
            raise ValueError(f"Component {component.identifier} has no inputs")

        return data

    def encode_outputs(self, circuit: Circuit) -> List[int]:
        data: List[int] = []
        for wire in circuit.outputs.values():
            wiring = self.encode_component_wiring(circuit.components, wire)
            data.extend(wiring)
        return data

    def encode_component_wiring(self, components: CircuitDict, wire: Wire) -> List[int]:
        data: List[int] = []

        length_data = len(data)
        for idx, subcomponent in enumerate(components.values()):
            wires_ids = [wire.id for wire in subcomponent.outputs.values()]
            if wire.id in wires_ids:
                # index of the subcomponent
                data.append(idx)
                # index of the wire in the subcomponent outputs
                data.append(wires_ids.index(wire.id))
                break
        if length_data == len(data):
            raise ValueError(f"Wire {wire.id} not found in any subcomponent outputs")
        return data
