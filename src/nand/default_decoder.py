from bitarray import bitarray

from nand.circuit import Circuit, CircuitId
from nand.circuit_decoder import CircuitDecoder
from nand.decoded_circuit import (
    ConnectionParameters,
    DecodedCircuit,
    InputParameters,
)
from nand.schematics import Schematics
from nand.wire import Wire


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
        nand_gate = Circuit(0)
        nand_gate.inputs[0] = Wire()
        nand_gate.inputs_names[0] = "0"
        nand_gate.inputs[1] = Wire()
        nand_gate.inputs_names[1] = "1"
        nand_gate.outputs[0] = Wire()
        nand_gate.outputs_names[0] = "0"

        self.schematics.add_schematic(nand_gate)

    def decode(self) -> Schematics:
        """Decode the data into circuits."""
        while len(self.data) != 0:
            # The index is used as the identifier of the circuit
            self.idx += 1
            # The current circuit being decoded
            self.circuit = DecodedCircuit(self.idx)
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

    def _decode_component(self, idx: int):
        """Decode the idx-th component of the circuit."""
        id = self.data.pop(0)
        try:
            component = self.schematics.get_schematic(id)
        except ValueError as e:
            raise ValueError(f"Trying to use the undefined component {id}.") from e
        self.circuit.add_component(idx, component)
        self._decode_component_inputs(idx, component)

    def _decode_component_inputs(self, component_idx: int, component: Circuit):
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

    def _decode_circuit_provenance(self, input_idx: int, component_idx: int):
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
            InputParameters(circuit_input_idx, component_idx, input_idx)
        )

    def _decode_component_provenance(self, input_idx: int, component_idx: int):
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
            ConnectionParameters(
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
