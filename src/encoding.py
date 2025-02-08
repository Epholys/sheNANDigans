from re import sub


class CircuitEncoder:
    def __init__(self, library):
        self.library = library
        self.circuits_ids = list(library.keys())

    def encode(self):
        data = []
        for idx, circuit in enumerate(self.library.values()):
            data.append(f"begin circuit")
            data.extend(self.encode_circuit(idx, circuit))
            data.append(f"end circuit")
        return data

    def encode_circuit(self, idx, circuit):
        if idx == 0:
            return []

        data = []
        data.append("begin header")
        data.extend(self.encode_header(idx, circuit))
        data.append("end header//begin components")
        for component in circuit.components.values():
            data.extend(self.encode_component(component, circuit))
            data.append('/')
        data.append("end components//begin outputs")
        data.extend(self.encode_outputs(circuit))
        data.append("end outputs")
        return data

    def encode_header(self, idx, circuit):
        data = []
        data.append(idx)
        data.append(len(circuit.components))
        data.append(len(circuit.inputs))
        data.append(len(circuit.outputs))
        return data

    def encode_component(self, component, circuit):
        data = []
        circuits_input_wires_id = [wire.id for wire in circuit.inputs.values()]

        print(f"encode_component(): encoding component of identifier {component.identifier} :\n{component} ")
        print(f"encode_component(): searching this identifier in circuit_ids {self.circuits_ids}")    
        print(f"encode_component(): found: {self.circuits_ids.index(component.identifier)}")

        # Encode component id
        data.append(self.circuits_ids.index(component.identifier))
        
        # Encode input wires
        print(f"encode_component(): encoding inputs {component.inputs}")
        length_data = len(data)
        for wire in component.inputs.values():
            print(f"encode_component(): searching wire {repr(wire)} in inputs")
            if wire.id in circuits_input_wires_id:
                # Provenance
                print(f"encode_component(): wire found in circuits inputs")
                print(f"encode_component(): provenance 0 ; idx {circuits_input_wires_id.index(wire.id)}")
                #data.append('prvn:')
                data.append(0)
                #data.append('input idx:')
                data.append(circuits_input_wires_id.index(wire.id))
            else:
                subcomponents = circuit.components
                print(f"encode_component(): trying to find wires in subcomponents outputs")
                #data.append('prvn:')
                data.append(1)
                #data.append('wiring:idx_sub+idx_out:')
                wiring = self.encode_component_wiring(subcomponents, wire, True)
                data.extend(wiring)
                print(f"encode_component(): provenance 1 ; idx sub + idx out {wiring}")
        if length_data == len(data):
            raise ValueError(f"Component {component.identifier} has no inputs")

        # Encode output wires
        # print(f"encode_component(): encoding outputs {component.outputs}")
        # length_data = len(data)
        # for wire in component.outputs.values():
        #     print(f"encode_component(): searching wire {repr(wire)} in outputs")
        #     if wire.id in circuits_output_wires_id:
        #         # Provenance
        #         print(f"encode_component(): wire found in circuits output")
        #         data.append(0)
        #         data.append(circuits_output_wires_id.index(wire.id))
        #     else:
        #         print(f"encode_component(): wire found in subcomponents output")
        #         data.append(1)
        #         data.extend(self.encode_component_wiring(subcomponents, wire, True))
        # if length_data == len(data):
        #     raise ValueError(f"Component {component.identifier} has no inputs")

        return data
    
    def encode_outputs(self, circuit):
        data = []
        print(f"encode_outputs(): encoding outputs {circuit.outputs}")
        for wire in circuit.outputs.values():
            print(f"encode_outputs(): trying to find wire {repr(wire)}:")
            wiring = self.encode_component_wiring(circuit.components, wire, True)
            data.extend(wiring)
            print(f"encode_outputs(): wiring {repr(wiring)}:")
        return data

    def encode_component_wiring(self, components, wire, inOutputs):
        data = []

        print(f"encode_component_wiring(): searching wire {repr(wire)} in components:\n{components}")
        length_data = len(data)
        for idx, subcomponent in enumerate(components.values()):
            wires_ids = []
            if inOutputs:
                wires_ids = [wire.id for wire in subcomponent.outputs.values()]
            if not inOutputs:
                wires_ids = [wire.id for wire in subcomponent.inputs.values()]
            if wire.id in wires_ids:
                # index of the subcomponent
                print(f"encode_component_wiring(): found {repr(wire)} in the {idx}-th subcomponent:\n{subcomponent}")
                data.append(idx)
                # index of the wire in the subcomponent outputs
                data.append(wires_ids.index(wire.id))
                break
        if length_data == len(data):
            raise ValueError(f"Wire {wire.id} not found in any subcomponent outputs")
        return data