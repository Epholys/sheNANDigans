from bitarray import bitarray

from nand.bit_packed_encoder import bitlength_with_offset
from nand.bits_utils import read_bits, read_bits_with_offset
from nand.circuit import Circuit
from nand.circuit_decoder import CircuitDecoder
from nand.decoded_circuit import ConnectionParameters, DecodedCircuit, InputParameters
from nand.schematics import Schematics


class BitPackedDecoder(CircuitDecoder):
    """
    Decode the bit-packed data into circuits.

    This decoder is designed to work with the output of `BitPackedEncoder`.
    The encoding is a compressed binary format where integer size in bits are optimized
    based on the overall structure of the circuit library. By conserving the minimum
    number of bits to encode the largest integer, but also by offsetting by one:
    in a lot of cases, a value of 0 is nonsense, so the encoding '0' is decoded
    as the value 1, the encoding '1' as the value 2, etc.

    The encoding is destructive, meaning the original names of circuits, inputs,
    and outputs are not preserved. They are identified by their index during decoding.
    However, the functional order is maintained.

    The format consists of a global header followed by a sequence of circuit
    definitions. The global header contains the bit sizes for various fields used
    throughout the rest of the data, allowing for a compact representation.

    'BitPackedEncoder' comments are the source of truth, so this class is voluntarily
    less commented.
    """

    def __init__(self):
        self.schematics = Schematics()
        self.schematics.add_schematic(self._build_nand())
        self.idx = 0

    def decode(self, data: bitarray) -> Schematics:
        """Decode the data into circuits."""
        self.data = list(data.tolist())

        self._decode_global_header()
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

    def _decode_global_header(self):
        """Decode the global header of the bit stream.

        The global header defines the bit widths for several key fields:
        - header_bitlength: The number of bits used to encode the bit widths themselves.
        - circuits_bitlength: The number of bits for a circuit identifier.
        - max_components_bitlength: The number of bits for the count of components in a
          circuit.
        - max_inputs_bitlength: The number of bits for the count of inputs in a circuit.
        - max_outputs_bitlength: The number of bits for the count of outputs in a circuit.
        """
        header_bitlength = read_bits_with_offset(self.data, 2)
        self.circuits_bitlength = read_bits_with_offset(self.data, header_bitlength)
        self.max_components_bitlength = read_bits_with_offset(
            self.data, header_bitlength
        )
        self.max_inputs_bitlength = read_bits_with_offset(self.data, header_bitlength)
        self.max_outputs_bitlength = read_bits_with_offset(self.data, header_bitlength)

    def _decode_circuit(self):
        """Decode a single circuit from the data stream."""
        self._decode_circuit_header()
        for idx in range(0, self.circuit.components_count):
            self._decode_component(idx)
        self._decode_outputs()

    def _decode_circuit_header(self):
        """Decode the header for the current circuit.

        This header contains the number of components, inputs, and outputs for this
        specific circuit. From these counts, we can determine the bit widths needed
        for component indices, input indices, and output indices within this circuit's
        scope.
        """
        self.circuit.components_count = read_bits_with_offset(
            self.data, self.max_components_bitlength
        )
        self.components_bitlength = bitlength_with_offset(self.circuit.components_count)

        self.circuit.inputs_count = read_bits_with_offset(
            self.data, self.max_inputs_bitlength
        )
        self.inputs_bitlength = bitlength_with_offset(self.circuit.inputs_count)

        self.circuit.outputs_count = read_bits_with_offset(
            self.data, self.max_outputs_bitlength
        )
        self.outputs_bitlength = bitlength_with_offset(self.circuit.outputs_count)

    def _decode_component(self, component_idx: int):
        """Decode the component_idx-th component of the circuit."""
        circuit_id = read_bits(self.data, self.circuits_bitlength)
        try:
            component = self.schematics.get_schematic(circuit_id)
        except ValueError as e:
            raise ValueError(
                f"Trying to use the undefined component {circuit_id}."
            ) from e
        self.circuit.add_component(component_idx, component)
        self._decode_component_inputs(component_idx, component)

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
        circuit_input_idx = read_bits(self.data, self.inputs_bitlength)
        if circuit_input_idx >= self.circuit.inputs_count:
            raise ValueError(
                f"Circuit {self.circuit.identifier}: the {component_idx}-th component "
                f"asked for its {input_idx}-th input the {circuit_input_idx}-th input "
                f"of the circuit itself, which does not exists "
                f"(there is {self.circuit.inputs_count} inputs)."
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
        for output_idx in range(0, self.circuit.outputs_count):
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
        source_idx = read_bits(self.data, self.components_bitlength)

        if source_idx >= self.circuit.components_count:
            raise ValueError(
                f"The {source_idx}-th component does not exist "
                f"(there is {self.circuit.components_count} components)."
            )

        source_output_idx = read_bits(self.data, self.outputs_bitlength)

        return (source_idx, source_output_idx)
