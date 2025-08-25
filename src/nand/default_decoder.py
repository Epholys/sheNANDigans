from typing import List, NamedTuple

from bitarray import bitarray

from nand.circuit import Circuit, CircuitKey
from nand.circuit_decoder import CircuitDecoder
from nand.schematics import Schematics
from nand.wire import Wire


class _InputParameters(NamedTuple):
    """The parameters to connect an input of a circuit."""

    input_index: int
    component_key: CircuitKey
    component_input: int


class _ConnectionParameters(NamedTuple):
    """The parameters to connect two components."""

    source_key: int
    source_output: int
    target_key: CircuitKey
    target_input: int


class _DecodedCircuit(Circuit):
    """An intermediate class to decode a circuit.

    It contains information that is not in the Circuit class,
    but is necessary to decode a circuit, or at least to
    check the correctness of the encoded data.

    Attributes:
        n_components: The number of components in the circuit.
        n_inputs: The number of inputs in the circuit.
        n_outputs: The number of outputs in the circuit.
        stashed_inputs: The inputs that are stashed to be connected later.
        stashed_connections: The connections that are stashed to be connected later.
    """

    def __init__(self, identifier: CircuitKey):
        super().__init__(identifier)
        self.n_components = 0
        self.n_inputs = 0
        self.n_outputs = 0
        self.stashed_inputs: List[_InputParameters] = []
        self.stashed_connections: List[_ConnectionParameters] = []

    def stash_input(self, input: _InputParameters):
        """Stash a circuit's input to connect it later."""
        self.stashed_inputs.append(input)

    def apply_inputs(self):
        """Connect the inputs according to their input_index.

        The index is at the same time the ordering and the identifier of the input.

        This is necessary because the encoding does not define the inputs themselves.
        They are implicitly defined by their appearance during the decoding of the
        component's inputs. But these appearances are not necessarily in order, so
        we need to stash them and connect them later. Otherwise, the inputs order is
        mixed, and the decoded circuit is incorrect.
        """
        self.stashed_inputs.sort(key=lambda x: x.input_index)
        for input in self.stashed_inputs:
            self.connect_input(
                input.input_index,
                input.component_key,
                input.component_input,
            )

    def stash_connection(self, connection: _ConnectionParameters):
        """Stash a connection to apply it later."""
        self.stashed_connections.append(connection)

    def apply_connections(self):
        """Apply the stashed connections.

        This is necessary because the components can refer to other components
        that are not decoded yet. As such, we need to stash the connections
        and apply them later.
        """
        for connection in self.stashed_connections:
            self.connect(
                connection.source_key,
                connection.source_output,
                connection.target_key,
                connection.target_input,
            )


class DefaultDecoder(CircuitDecoder):
    """
    Decode the data into circuits.

    Please look at the CircuitEncoder as a reference for the encoding format.

    One important point to reiterate is that the names of the circuits, inputs,
    and outputs are lost during the encoding. They are replaced by the index in which
    they appear. But that order, which defines the functionality, is preserved.
    """

    def __init__(self, data: bitarray):
        """
        Initializes the decoder with the bitarray data.

        Args:
            data: The bitarray containing the encoded circuit library.
        """
        self.data = list(data.tobytes())
        self.schematics = Schematics()

        self._add_nand()  # TODO merge with schematics.add_nand

        self.idx = 0

    def _add_nand(self):
        """Add the base NAND gate."""
        nand_gate = Circuit(0)
        nand_gate.inputs[0] = Wire()
        nand_gate.inputs[1] = Wire()
        nand_gate.outputs[0] = Wire()
        self.schematics.add_schematic(nand_gate)

    def decode(self) -> Schematics:
        """Decode the data into circuits."""
        while len(self.data) != 0:
            # The index is used as the identifier of the circuit
            self.idx += 1
            # The current circuit being decoded
            self.circuit = _DecodedCircuit(self.idx)
            self._decode_circuit()
            self.circuit.apply_inputs()
            self.circuit.apply_connections()
            self.schematics.add_schematic(self.circuit)
        return self.schematics

    def _decode_circuit(self):
        """Decode a single circuit from the data stream."""
        self._decode_header()
        for idx in range(0, self.circuit.n_components):
            self._decode_component(idx)
        self._decode_outputs()

    def _decode_header(self):
        """Decode the header of the current circuit."""
        self.circuit.n_components = self.data.pop(0)
        self.circuit.n_inputs = self.data.pop(0)
        self.circuit.n_outputs = self.data.pop(0)

    def _decode_component(self, idx: CircuitKey):
        """Decode the idx-th component of the circuit."""
        id = self.data.pop(0)
        try:
            component = self.schematics.get_schematic(id)
        except ValueError as e:
            raise ValueError(f"Trying to use the undefined component {id}.") from e
        self.circuit.add_component(idx, component)
        self._decode_component_inputs(idx, component)

    def _decode_component_inputs(self, component_idx: CircuitKey, component: Circuit):
        """Decode the inputs of 'component', the 'component_idx'-th component
        of the circuit.
        """
        for input_idx in range(0, len(component.inputs)):
            provenance = self.data.pop(0)
            if provenance == 0:
                self._decode_circuit_provenance(input_idx, component_idx)
            elif provenance == 1:
                self._decode_component_provenance(input_idx, component_idx)
            else:
                raise ValueError(
                    f"Provenance {provenance} is not recognized. It must be "
                    f"0 (circuit's inputs) or 1 (another component's inputs)."
                )

    def _decode_circuit_provenance(self, input_idx: int, component_idx: CircuitKey):
        """Decode the 'input_idx'-th input of the 'component_idx'-th component of the
        circuit, originating from the circuit's inputs.
        """
        circuit_input_idx = self.data.pop(0)
        if circuit_input_idx >= self.circuit.n_inputs:
            raise ValueError(
                f"Circuit {self.circuit.identifier}: the {component_idx}-th component "
                f"asked for its {input_idx}-th input the {circuit_input_idx}-th input "
                f"of the circuit itself, which does not exists "
                f"(there is {self.circuit.n_inputs} inputs)."
            )

        self.circuit.stash_input(
            _InputParameters(circuit_input_idx, component_idx, input_idx)
        )

    def _decode_component_provenance(self, input_idx: int, component_idx: CircuitKey):
        """Decode the 'input_idx'-th input of the 'component_idx'-th component of the
        circuit, originating from another component's outputs.
        """
        try:
            (source_idx, source_output_idx) = self._decode_component_wiring()
        except ValueError as e:
            raise ValueError(
                f"Circuit {self.circuit.identifier}: the {component_idx}-th component "
                f"asked for its {input_idx}-th input an output from a component that "
                f"does not exists "
            ) from e

        self.circuit.stash_connection(
            _ConnectionParameters(
                source_idx,
                source_output_idx,
                component_idx,
                input_idx,
            )
        )

    def _decode_outputs(self):
        """Decode the outputs of the current decoded circuit.
        They must come from one of its component.
        """
        for output_idx in range(0, self.circuit.n_outputs):
            try:
                (source_idx, source_output_idx) = self._decode_component_wiring()
            except ValueError as e:
                raise ValueError(
                    f"Circuit {self.circuit.identifier} asked for its {output_idx}-th "
                    f"output an output from a component that does not exists."
                ) from e

            self.circuit.connect_output(output_idx, source_idx, source_output_idx)

    def _decode_component_wiring(self):
        """Decode the wiring between components: the component index
        and its output index.
        """
        source_idx = self.data.pop(0)

        if source_idx >= self.circuit.n_components:
            raise ValueError(
                f"The {source_idx}-th component does not exist "
                f"(there is {self.circuit.n_components} components)."
            )

        source_output_idx = self.data.pop(0)

        return (source_idx, source_output_idx)
