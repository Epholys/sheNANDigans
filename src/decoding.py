from typing import List, NamedTuple, OrderedDict

import schematics
from circuit import Circuit, CircuitDict, CircuitKey, Wire


class _UnorderedInput(NamedTuple):
    input_index: int
    component_key: CircuitKey
    component_input: int


class DecodedCircuit(Circuit):
    def __init__(self, identifier: CircuitKey):
        super().__init__(identifier)
        self.n_components = 0
        self.n_inputs = 0
        self.n_outputs = 0
        self.unordered_inputs: List[_UnorderedInput] = []

    def stash_input(self, input: _UnorderedInput):
        self.unordered_inputs.append(input)

    def order_inputs(self):
        self.unordered_inputs.sort(key=lambda x: x.input_index)
        for unordered_input in self.unordered_inputs:
            self.connect_input(
                unordered_input.input_index,
                unordered_input.component_key,
                unordered_input.component_input,
            )

    def validate(self) -> bool:
        return super().validate()


class CircuitDecoder:
    def __init__(self, data: List[int]):
        self.data = data.copy()
        self.library: CircuitDict = OrderedDict()

        self.add_nand()

        self.idx = 0

    def add_nand(self):
        nand_gate = Circuit(0)
        nand_gate.inputs[0] = Wire()
        nand_gate.inputs[1] = Wire()
        nand_gate.outputs[0] = Wire()
        schematics.add_schematic(nand_gate, self.library)

    def decode(self) -> CircuitDict:
        while len(self.data) != 0:
            self.idx += 1
            self.circuit = DecodedCircuit(self.idx)
            self.decode_circuit()
            self.circuit.validate()
            schematics.add_schematic(self.circuit, self.library)
            self.circuit.order_inputs()

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

    def decode_component(self, idx_component: CircuitKey):
        component_id = self.data.pop(0)
        if component_id not in self.library.keys():
            raise ValueError(f"Trying to use the undefined component {component_id}")
        component = schematics.get_schematic(component_id, self.library)
        self.circuit.add_component(idx_component, component)
        self.decode_inputs(idx_component, component)

    def decode_inputs(self, idx_component: CircuitKey, component: Circuit):
        for component_in_idx in range(0, len(component.inputs)):
            provenance = self.data.pop(0)
            if provenance == 0:
                circuit_in_idx = self.data.pop(0)
                if circuit_in_idx >= self.circuit.n_inputs:
                    raise ValueError(
                        f"{idx_component}-th component of circuit {self.circuit.identifier} asked for the {component_in_idx}-th input, which is not in 0..{self.circuit.n_inputs}"
                    )
                self.circuit.stash_input(
                    _UnorderedInput(circuit_in_idx, idx_component, component_in_idx)
                )
            else:
                other_component_id = self.data.pop(0)
                other_component_out_idx = self.data.pop(0)
                if other_component_id >= self.circuit.n_components:
                    raise ValueError(
                        f"{idx_component}-th component of circuit {self.circuit.identifier} asked for an output of component {other_component_id}, which does not exists"
                    )
                if other_component_out_idx > len(component.outputs):
                    raise ValueError(
                        f"{idx_component}-th component of circuit {self.circuit.identifier} asked for the {other_component_out_idx}-th output of component {other_component_id}, which is not in 0..{len(component.outputs)}"
                    )
                self.circuit.connect(
                    other_component_id,
                    other_component_out_idx,
                    idx_component,
                    component_in_idx,
                )

    def decode_outputs(self):
        for output_idx in range(0, self.circuit.n_outputs):
            component_id = self.data.pop(0)
            if self.library.get(component_id) is None:
                raise ValueError(f"Circuit {component_id} does not exist")
            component = self.library[component_id]

            component_out_idx = self.data.pop(0)
            if component_id >= self.circuit.n_components:
                raise ValueError(
                    f"The circuit {self.circuit.identifier} asked for its {output_idx}-th output on those of {component_id}, which does not exists"
                )
            if component_out_idx > len(component.outputs):
                raise ValueError(
                    f"The circuit {self.circuit.identifier} asked for its {output_idx}-th output the {component_out_idx}-th of component {component_id}, which is not in 0..{len(component.outputs)}"
                )

            self.circuit.connect_output(output_idx, component_id, component_out_idx)
