from bitarray import bitarray

from nand.bit_packed_encoder import bitlength_with_offset
from nand.bits_utils import bits2int, bits2int_with_offset
from nand.circuit import Circuit
from nand.circuit_decoder import CircuitDecoder
from nand.decoded_circuit import ConnectionParameters, DecodedCircuit, InputParameters
from nand.schematics import Schematics
from nand.wire import Wire


class BitPackedDecoder(CircuitDecoder):
    """
    Decode the bit-packed data into circuits.

    This decoder is designed to work with the output of `BitPackedEncoder`.
    The encoding is a compressed binary format where integer sizes are optimized
    based on the overall structure of the circuit library.

    The encoding is destructive, meaning the original names of circuits, inputs,
    and outputs are not preserved. They are identified by their index during decoding.
    However, the functional order is maintained.

    The format consists of a global header followed by a sequence of circuit
    definitions. The global header contains the bit sizes for various fields used
    throughout the rest of the data, allowing for a compact representation.
    """

    def __init__(self, data: bitarray):
        self.data = list(data.tolist())
        self.schematics = Schematics()

        self._add_nand()
        self._decode_global_header()

        self.idx = 0

    def _decode_global_header(self):
        """Decode the global header of the bit stream.

        The global header defines the bit widths for several key fields:
        - bits_max: The number of bits used to encode the bit widths themselves.
        - bit_circuits: The number of bits for a circuit identifier.
        - max_bit_components: The number of bits for the count of components in a
          circuit.
        - max_bit_inputs: The number of bits for the count of inputs in a circuit.
        - max_bit_outputs: The number of bits for the count of outputs in a circuit.
        """
        bits_max = bits2int_with_offset(self.data, 2)
        self.bit_circuits = bits2int_with_offset(self.data, bits_max)
        self.max_bit_components = bits2int_with_offset(self.data, bits_max)
        self.max_bit_inputs = bits2int_with_offset(self.data, bits_max)
        self.max_bit_outputs = bits2int_with_offset(self.data, bits_max)

    def _add_nand(self):
        """Add the base NAND gate."""
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
        while len(self.data) > 0:
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
        self._decode_circuit_header()
        for idx in range(0, self.circuit.n_components):
            self._decode_component(idx)
        self._decode_outputs()

    def _decode_circuit_header(self):
        """Decode the header for the current circuit.

        This header contains the number of components, inputs, and outputs for this
        specific circuit. From these counts, we can determine the bit widths needed
        for component indices, input indices, and output indices within this circuit's
        scope.
        """
        # TODO : explain the offsets.
        self.circuit.n_components = bits2int_with_offset(
            self.data, self.max_bit_components
        )
        self.bl_components = bitlength_with_offset(self.circuit.n_components)

        self.circuit.n_inputs = bits2int_with_offset(self.data, self.max_bit_inputs)
        self.bl_inputs = bitlength_with_offset(self.circuit.n_inputs)

        self.circuit.n_outputs = bits2int_with_offset(self.data, self.max_bit_outputs)
        self.bl_outputs = bitlength_with_offset(self.circuit.n_outputs)

    def _decode_component(self, idx: int):
        """Decode the idx-th component of the circuit."""
        id = bits2int(self.data, self.bit_circuits)
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
                    f"0 (circuit's inputs) or 1 (another component's outputs)."
                )

    def _decode_circuit_provenance(self, input_idx: int, component_idx: int):
        """Decode the 'input_idx'-th input of the 'component_idx'-th component of the
        circuit, originating from the circuit's inputs.
        """
        circuit_input_idx = bits2int(self.data, self.bl_inputs)
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
        They must come from one of its components.
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
        """Decode the wiring between components: the source component index
        and its output index.
        """
        source_idx = bits2int(self.data, self.bl_components)

        if source_idx >= self.circuit.n_components:
            raise ValueError(
                f"The {source_idx}-th component does not exist "
                f"(there is {self.circuit.n_components} components)."
            )

        source_output_idx = bits2int(self.data, self.bl_outputs)

        return (source_idx, source_output_idx)
