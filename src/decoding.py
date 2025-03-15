from typing import List, NamedTuple, OrderedDict

import schematics
from circuit import Circuit, CircuitDict, CircuitKey
from wire import WireFast


class _InputParameters(NamedTuple):
    """
    The parameters to connect an input to a circuit.

    The rational is that the inputs' order must be preserved from the encoded circuit,
    but the encoded inputs are not necessarily in order. As such, we stash them and connect them later.
    """

    input_index: int
    component_key: CircuitKey
    component_input: int


class _ConnectionParameters(NamedTuple):
    """ """

    source_key: int
    source_output: int
    target_key: CircuitKey
    target_input: int


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
        self.stashed_connections: List[_ConnectionParameters] = []

    def stash_input(self, input: _InputParameters):
        """
        Stash an input to connect it later.
        """
        self.stashed_inputs.append(input)

    def apply_inputs(self):
        """
        Connect the inputs according to their input_index.

        Note : the index is at the same time the ordering and the identifier of the input.
        """
        self.stashed_inputs.sort(key=lambda x: x.input_index)
        for input in self.stashed_inputs:
            self.connect_input(
                input.input_index,
                input.component_key,
                input.component_input,
            )

    def stash_connection(self, connection: _ConnectionParameters):
        """
        Stash an input to connect it later.
        """
        self.stashed_connections.append(connection)

    def apply_connections(self):
        """
        Connect the inputs according to their input_index.

        Note : the index is at the same time the ordering and the identifier of the input.
        """
        for connection in self.stashed_connections:
            self.connect(
                connection.source_key,
                connection.source_output,
                connection.target_key,
                connection.target_input,
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
        nand_gate.inputs[0] = WireFast()
        nand_gate.inputs[1] = WireFast()
        nand_gate.outputs[0] = WireFast()
        schematics.add_schematic(nand_gate, self.library)

    def decode(self) -> CircuitDict:
        while len(self.data) != 0:
            # The index is used as the identifier of the circuit
            self.idx += 1
            # The current circuit being decoded
            self.circuit = DecodedCircuit(self.idx)
            self.decode_circuit()
            self.circuit.validate()
            self.circuit.apply_inputs()
            self.circuit.apply_connections()
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
                f"Circuit {self.circuit.identifier}: the {component_idx}-th component asked for its {input_idx}-th input the {circuit_input_idx}-th input of the circuit itself, which is not in [0, {self.circuit.n_inputs}[."
            )
        self.circuit.stash_input(
            _InputParameters(circuit_input_idx, component_idx, input_idx)
        )

    def decode_component_provenance(self, input_idx: int, component_idx: CircuitKey):
        """
        Decode the 'input_idx'-th input of the 'component_idx'-th component of the circuit, originating from another component's outputs.
        """
        (source_idx, source_output_idx) = self.decode_component_wiring()

        print(len(self.circuit.components)) if self.circuit.identifier == 10 else ""

        if source_output_idx is None:
            raise ValueError(
                f"Circuit {self.circuit.identifier}: the {component_idx}-th component asked for its {input_idx}-th input an output of {source_idx}-th component , which is not in [0,  {len(self.circuit.components)}[."
            )

        self.circuit.stash_connection(
            _ConnectionParameters(
                source_idx,
                source_output_idx,
                component_idx,
                input_idx,
            )
        )

    def decode_outputs(self):
        """
        Decode the outputs of the current decoded circuit. They must come from one its component.
        """
        for output_idx in range(0, self.circuit.n_outputs):
            (source_idx, source_output_idx) = self.decode_component_wiring()

            if source_output_idx is None:
                raise ValueError(
                    f"Circuit {self.circuit.identifier} asked for its {output_idx}-th output the {source_output_idx}-th output of its {source_idx}-th component,  which does not exist."
                )

            self.circuit.connect_output(output_idx, source_idx, source_output_idx)

    def decode_component_wiring(self):
        """
        Decode the wiring between components: the component index and its output index.
        The 'None' are here to indicate error so that the callers can raise an Exception with a meaningful message.
        """
        source_idx = self.data.pop(0)
        if source_idx >= self.circuit.n_components:
            print(source_idx)
            print(len(self.circuit.components))
            return (source_idx, None)

        source_output_idx = self.data.pop(0)

        return (source_idx, source_output_idx)
