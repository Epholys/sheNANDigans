from typing import List, NamedTuple, OrderedDict

import schematics
from circuit import Circuit, CircuitDict, CircuitKey, Wire


class _InputParameters(NamedTuple):
    """
    The parameters to connect an input to a circuit.

    The rational is that the inputs' order must be preserved from the encoded circuit,
    but the encoded inputs are not necessarily in order. As such, we stash them and connect them later.
    """

    input_index: int
    component_key: CircuitKey
    component_input: int


class DecodedCircuit(Circuit):
    """
    An intermediate class to decode a circuit.

    It contains data that is not in the Circuit class, but is necessary to decode a circuit.
    """

    def __init__(self, identifier: CircuitKey):
        super().__init__(identifier)
        self.n_components = 0
        self.n_inputs = 0
        self.n_outputs = 0
        self.stashed_inputs: List[_InputParameters] = []

    def stash_input(self, input: _InputParameters):
        """
        Stash an input to connect it later.
        """
        self.stashed_inputs.append(input)

    def order_inputs(self):
        """
        Connect the inputs according to their input_index.

        Note : the index is at the same time the ordering and the identifier of the input.
        """
        self.stashed_inputs.sort(key=lambda x: x.input_index)
        for unordered_input in self.stashed_inputs:
            self.connect_input(
                unordered_input.input_index,
                unordered_input.component_key,
                unordered_input.component_input,
            )

    def validate(self) -> bool:
        return super().validate()


class CircuitDecoder:
    """
    Decode the data into circuits.

    Please look at the CircuitEncoder to understand the encoding format.

    One point important to reiterate is that the names of the circuits, inputs, and outputs are lost during the encoding. They are replaced by the index in which their appear. But the order, that defines the functionality, is preserved.
    """

    def __init__(self, data: List[int]):
        self.data = data.copy()
        self.library: CircuitDict = OrderedDict()

        self.add_nand()  # TODO merge with schematics.addnand

        self.idx = 0

    def add_nand(self):
        nand_gate = Circuit(0)
        nand_gate.inputs[0] = Wire()
        nand_gate.inputs[1] = Wire()
        nand_gate.outputs[0] = Wire()
        schematics.add_schematic(nand_gate, self.library)

    def decode(self) -> CircuitDict:
        while len(self.data) != 0:
            # The index is used as the identifier of the circuit
            self.idx += 1
            # The current circuit being decoded
            self.circuit = DecodedCircuit(self.idx)
            self.decode_circuit()
            self.circuit.validate()
            self.circuit.order_inputs()
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

    def decode_component(self, idx: CircuitKey):
        """
        Decode the idx-th component of the circuit.
        """
        id = self.data.pop(0)
        if id not in self.library.keys():
            raise ValueError(f"Trying to use the undefined component {id}.")
        component = schematics.get_schematic(id, self.library)
        self.circuit.add_component(idx, component)
        self.decode_inputs(idx, component)

    def decode_inputs(self, component_idx: CircuitKey, component: Circuit):
        """
        Decode the inputs of 'component', the 'component_idx'-th component of the circuit.
        """
        for input_idx in range(0, len(component.inputs)):
            provenance = self.data.pop(0)
            if provenance == 0:
                self.decode_circuit_provenance(input_idx, component_idx)
            elif provenance == 1:
                self.decode_component_provenance(input_idx, component_idx)
            else:
                raise ValueError(
                    f"Provenance {provenance} is not recognized. It must be 0 (circuit's inputs) or 1 (another component inputs)."
                )

    def decode_circuit_provenance(self, input_idx: int, component_idx: CircuitKey):
        """
        Decode the 'input_idx'-th input of the 'component_idx'-th component of the circuit, originating from the circuit's inputs.
        """
        circuit_input_idx = self.data.pop(0)
        if circuit_input_idx >= self.circuit.n_inputs:
            raise ValueError(
                f"Circuit {self.circuit.identifier}: the {component_idx}-th component asked for its {input_idx}-th input the {circuit_input_idx}-th input of the circuit itself, which is not in 0..{self.circuit.n_inputs}."
            )
        self.circuit.stash_input(
            _InputParameters(circuit_input_idx, component_idx, input_idx)
        )

    def decode_component_provenance(self, input_idx: int, component_idx: CircuitKey):
        """
        Decode the 'input_idx'-th input of the 'component_idx'-th component of the circuit, originating from another component's outputs.
        """
        source_id = self.data.pop(0)
        if source_id not in self.library.keys():
            raise ValueError(
                f"Circuit {self.circuit.identifier}: the {component_idx}-th component asked for its {input_idx}-th input an output of component {source_id}, which does not exists."
            )
        source = self.library[source_id]

        source_output_idx = self.data.pop(0)
        if source_output_idx > len(source.outputs):
            raise ValueError(
                f"Circuit {self.circuit.identifier}: the {component_idx}-th component asked for its {input_idx}-th input the {source_output_idx}-th output of component {source_id}, which is not in 0..{len(source.outputs)}."
            )
        self.circuit.connect(
            source_id,
            source_output_idx,
            component_idx,
            input_idx,
        )

    def decode_outputs(self):
        """
        Decode the outputs of the current decoded circuit. They must come from one its component.
        """
        for output_idx in range(0, self.circuit.n_outputs):
            source_idx = self.data.pop(0)
            if source_idx >= self.circuit.n_components:
                raise ValueError(
                    f"Circuit {self.circuit.identifier} asked for its {output_idx}-th output to come from its {source_idx}-th component, which is not in 0..{self.circuit.n_components}."
                )

            source_output_idx = self.data.pop(0)
            try:
                self.circuit.connect_output(output_idx, source_idx, source_output_idx)
            except ValueError as _:
                raise ValueError(
                    f"Circuit {self.circuit.identifier} asked for its {output_idx}-th output the {source_output_idx}-th output of its {source_idx}-th component, which does not exists."
                )
