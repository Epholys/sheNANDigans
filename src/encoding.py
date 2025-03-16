from copy import deepcopy
from typing import List

from circuit import Circuit, CircuitDict, Wire


class CircuitEncoder:
    """
    Encode a circuit library into a list of integers.

    This is a relatively simple, not fully optimized, encoding.
    But it has some little tricks to reduce the size of the encoding.

    The encoding itself is described in the encoding methods, as it's done in one pass.

    The encoding is destructive, in the way that the names of the components, inputs and outputs are not encoded.
    Instead, their indexes are encoded, and these will become the new "names" during decoding.  But the order, that defines the functionality, is preserved.

    TODO add a reference to the circuit wiring model
    """

    def __init__(self, library: CircuitDict):
        self.library: CircuitDict = deepcopy(library)
        self.encoding: List[int]
        # TODO add validation for all circuits of library ?
        # It would minimize safety checks

    def encode(self) -> List[int]:
        """
        library = [circuit_1, circuit_2, ...]
        Note : circuit_0 is the nand gate, and not encoded as it is supposed here by default
        """
        self.encoding = []
        for circuit in self.library.values():
            if circuit.identifier == 0:
                continue
            self.encode_circuit(circuit)
        return self.encoding

    def encode_circuit(self, circuit: Circuit):
        """
        circuit = [header, components, outputs]
        """
        self.encode_header(circuit)
        self.encode_components(circuit)
        self.encode_outputs(circuit)

    def encode_header(self, circuit: Circuit):
        """
        header = [n_components, n_inputs, n_outputs]
        n_components is used in decoding to know how many components to read
        n_inputs is used in decoding for safety check
        n_outputs is used in decoding to know how many outputs to read
        """
        self.encoding.append(len(circuit.components))
        self.encoding.append(len(circuit.inputs))
        self.encoding.append(len(circuit.outputs))

    def encode_components(self, circuit: Circuit):
        """
        components = [component_0, component_1, ..., component_n]
        """
        for component in circuit.components.values():
            self.encode_component(component, circuit)

    def encode_component(self, component: Circuit, circuit: Circuit):
        """
        component = [id, inputs]
        id is not the identifier of the circuit, but the index of the component in the circuit.
        But, during decoding this index becomes the identifier of the component.
        """
        circuit_ids = list(self.library.keys())
        self.encoding.append(circuit_ids.index(component.identifier))

        self.encode_inputs(component, circuit)

    def encode_inputs(self, component: Circuit, circuit: Circuit):
        """
        inputs = [input_0, input_1, ..., input_n]
        input = [provenance, location]

        provenance = 0 if the input is a circuit input, 1 if it is a component output
        location =
            if provenance = 0:
                location = index in the circuit inputs
            if provenance = 1:
                location = wiring (see encode_component_wiring())

        provenance seems to be useless (we could remove it and encode directly the location with a special value for circuit inputs),
        but it *will* be useful for the bit-packing optimization.
        """
        circuit_input = [wire.id for wire in circuit.inputs.values()]

        for input in component.inputs.values():
            if input.id in circuit_input:
                self.encoding.append(0)
                self.encoding.append(circuit_input.index(input.id))
            else:
                self.encoding.append(1)
                self.encode_component_wiring(input, circuit.components)

    def encode_outputs(self, circuit: Circuit):
        """
        outputs = [output_0, output_1, ..., output_n]
        output = wiring (see encode_component_wiring())
        """
        for output in circuit.outputs.values():
            self.encode_component_wiring(output, circuit.components)

    def encode_component_wiring(self, wire: Wire, components: CircuitDict):
        """
        wiring = [component_idx, output_idx]
        component_idx is the index of the component in the circuit
        output_idx is the index of the output in the component
        """
        for idx, subcomponent in enumerate(components.values()):
            outputs = [wire.id for wire in subcomponent.outputs.values()]
            if wire.id in outputs:
                self.encoding.append(idx)
                self.encoding.append(outputs.index(wire.id))
                return
        raise ValueError(f"Wire {wire.id} not found in any subcomponent outputs")
