
from nand.bit_packed_decoder import BitPackedDecoder
from nand.bits_utils import bitlength_with_offset, read_bits
from nand.circuit_encoder import BitArrayLike
from nand.decoded_circuit import ConnectionParameters, DecodedCircuit, InputParameters
from nand.circuit_library import CircuitLibrary

class FlattenedDecodedCircuit(DecodedCircuit):
    def __init__(self):
        super().__init__(-1)
        self.zero_one_flag: bool = False
        self.rolling_nand_bitlength: int = 1
        self.nand_count: int = 1
        self.nand_idx_map: dict[int, int] = {}

class FlattenedDecoder(BitPackedDecoder):
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
        super().__init__()
        self.circuit = FlattenedDecodedCircuit()

    def decode(self, data: BitArrayLike) -> CircuitLibrary:
        """Decode the data into circuits."""
        return super().decode(data)

    def _decode_circuit_header(self):
        """Decode the header for the current circuit.

        This header contains the number of components, inputs, and outputs for this
        specific circuit. From these counts, we can determine the bit widths needed
        for component indices, input indices, and output indices within this circuit's
        scope.
        """
        self.circuit.zero_one_flag = bool(read_bits(self.data, 1))
        super()._decode_circuit_header()

    def _decode_component(self, component_idx: int):
        """Decode the component_idx-th component of the circuit."""
        self.circuit.add_component(component_idx, self.library.get_circuit_from_idx(0))
        self._decode_nand_inputs(component_idx, component)

    def _decode_nand_inputs(self, nand_idx: int):
        for input_idx in range(2):
            first_provenance = self.data.pop(0)
            if first_provenance == 0:
                if not self.circuit.zero_one_flag:
                    self._decode_circuit_provenance(input_idx, nand_idx)
                else:
                    second_provenance = self.data.pop(0)
                    if second_provenance == 0:
                        self._decode_circuit_provenance(input_idx, nand_idx)
                    elif second_provenance == 1:
                        self._decode_zero_one_provenance(input_idx, nand_idx)
                    else:
                        raise ValueError(f"The second provenance for input {input_idx} of nand {nand_idx} "
                                        "with zero_one_flag must be 0 (circuit input) or 1 (zero/one).")
            elif first_provenance == 1:
                self._decode_component_provenance(input_idx, nand_idx)
            else:
                raise ValueError("The second provenance for input {input_idx} of nand {nand_idx} "
                                 "must be 0 (circuit/zero/one input) or 1 (other nand).")

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

    def _decode_zero_one_provenance(self, input_idx: int, nand_idx: int):
        third_provenance = self.data.pop(0)
        if third_provenance == 0:
            if not any([component.identifier == 1 for component in self.circuit.components.values()]):
                self.circuit.add_component(-1, self.library.get_circuit_from_idx(1))
            self.circuit.stash_connection(ConnectionParameters(-1, 0, nand_idx, input_idx))
        elif third_provenance == 1:
            if not any([component.identifier == 2 for component in self.circuit.components.values()]):
                self.circuit.add_component(-2, self.library.get_circuit_from_idx(2))
            self.circuit.stash_connection(ConnectionParameters(-2, 0, nand_idx, input_idx))


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

            self.circuit.connect_output(source_idx, source_output_idx, output_idx)

    def _decode_component_wiring(self):
        """Decode the wiring between components: the source component index
        and its output index.
        """
        source_idx = read_bits(self.data, self.circuit.rolling_nand_bitlength)

        self._update(source_idx)

        source_idx = read_bits(self.data, self.components_bitlength)

        if source_idx >= self.circuit.components_count:
            raise ValueError(
                f"The {source_idx}-th component does not exist "
                f"(there is {self.circuit.components_count} components)."
            )

        source_output_idx = read_bits(self.data, self.outputs_bitlength)

        return (source_idx, source_output_idx)

    def _update(self, source_idx: int):
        source_bitlength = bitlength_with_offset()


