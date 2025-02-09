from typing import OrderedDict

import schematics
from circuit import Circuit, Wire

class DecodedCircuit(Circuit):
    def __init__(self, identifier):
        super().__init__(identifier)
        self.n_components = 0
        self.n_inputs = 0
        self.n_outputs = 0

    def validate(self):
        super().validate()

class CircuitDecoder:
    def __init__(self, data):
        self.data = data
        self.library = OrderedDict()

        self.add_nand()

        self.idx = 0
        self.circuit = None        

    def add_nand(self):
        nand_gate = Circuit(0)
        nand_gate.inputs[0] = Wire()
        nand_gate.inputs[1] = Wire()
        nand_gate.outputs[0] = Wire()
        schematics.add_schematic(nand_gate, self.library)

    def decode(self):
        while len(self.data) != 0:
            self.idx += 1
            self.circuit = DecodedCircuit(self.idx)
            self.decode_circuit()
            self.circuit.validate()
            schematics.add_schematic(self.circuit, self.library)
        return self.library
    
    def decode_circuit(self):
        self.decode_header()
        for idx in range(0, self.circuit.n_components):
            self.decode_component(idx)
        self.decode_outputs()
        
    def decode_header(self):
        self.circuit.n_components = self.data.pop(0)
        self.circuit.n_inputs = self.data.pop(0)
        self.circuit.n_outputs = self.data.pop(0)

    def decode_component(self, idx_component):
        component_id = self.data.pop(0)
        if not component_id in self.library.keys():
            raise ValueError(f"Trying to use the undefined component {component_id}")
        component = schematics.get_schematic(component_id, self.library)
        # print(f"self.circuit.add_component({idx_component}, {component.identifier})")
        self.circuit.add_component(idx_component, component)
        self.decode_inputs(idx_component, component)

    def decode_inputs(self, idx_component, component):
        for component_in_idx in range(0, len(component.inputs)):
            provenance = self.data.pop(0)
            if provenance == 0:
                circuit_in_idx = self.data.pop(0)
                if circuit_in_idx >= self.circuit.n_inputs:
                    raise ValueError(f"{idx_component}-th component of circuit {self.circuit.identifier} asked for the {component_in_idx}-th input, which is not in 0..{self.circuit.n_inputs}")
                # print(f"self.circuit.add_input({circuit_in_idx}, {idx_component}, {component_in_idx})")
                self.circuit.add_input(circuit_in_idx, idx_component, component_in_idx)
            else:
                other_component_id = self.data.pop(0)
                other_component_out_idx = self.data.pop(0)
                if other_component_id >= self.circuit.n_components:
                    raise ValueError(f"{idx_component}-th component of circuit {self.circuit.identifier} asked for an output of component {other_component_id}, which does not exists")
                if other_component_out_idx > len(component.outputs):
                    raise ValueError(f"{idx_component}-th component of circuit {self.circuit.identifier} asked for the {other_component_out_idx}-th output of component {other_component_id}, which is not in 0..{len(component.outputs)}")
                # print(f"self.circuit.add_wire({other_component_id}, {other_component_out_idx}, {component.identifier}, {component_in_idx})")
                self.circuit.add_wire(other_component_id, other_component_out_idx, idx_component, component_in_idx)

    def decode_outputs(self):
        for output_idx in range(0, self.circuit.n_outputs):
            component_id = self.data.pop(0)
            if self.library.get(component_id) is None:
                raise ValueError(f"Circuit {component_id} does not exist")
            component = self.library[component_id]

            component_out_idx = self.data.pop(0)
            if component_id >= self.circuit.n_components:
                raise ValueError(f"The circuit {self.circuit.identifier} asked for its {output_idx}-th output on those of {component_id}, which does not exists")
            if component_out_idx > len(component.outputs):
                raise ValueError(f"The circuit {self.circuit.identifier} asked for its {output_idx}-th output the {component_out_idx}-th of component {component_id}, which is not in 0..{len(component.outputs)}")
            
            # print(f"self.circuit.add_output({output_idx}, {component_id}, {component_out_idx})")
            self.circuit.add_output(output_idx, component_id, component_out_idx)