from copy import deepcopy
from enum import Enum, auto
from typing import List, Tuple

from bitarray import bitarray

from nand.bits_utils import bitlength_with_offset, int2bitlist, int2bitlist_with_offset
from nand.circuit import Circuit, CircuitDict, Wire
from nand.circuit_encoder import CircuitEncoder
from nand.schematics import Schematics


class EncodedCircuitMetadata:
    def __init__(self):
        self.components_bitlength = 0
        self.inputs_bitlength = 0
        self.outputs_bitlength = 0


class Placeholder(Enum):
    """Placeholder category for the bitlength when it is not known yet."""

    COMPONENTS = auto()
    INPUTS = auto()
    OUTPUTS = auto()


class BitPackedEncoder(CircuitEncoder):
    """
    Encode a circuit library into a bitarray using bit-packing for compression.

    This encoder optimizes the storage space by determining the minimum number of bits
    required for various indices and counts across the entire library.

    There is a bit counting for each circuit, which is dynamically computed with the
    number of circuits, components, inputs, and outputs. The number of bits necessary
    for them is encoded in the circuit header.

    There is a second level bit counting, this time to know how many bits are necessary
    to encode *the number of bit necessary* for the count of circuits, components,
    inputs, and outputs for the circuits.

    Finally, there's a third level of bit counting, to know how many bits are necessary
    to encode the number the second level bit counting. It's two bit long.
    These last two levels are encoded in a global header.

    Note that there's an offset of 1 each time a value of '0' does not make any sense
    For example, 0 component, input, or output for a circuit is considered impossible.
    So, the encoding '0' will be decoded as the value 1, etc.
    For example, if we have a circuit with 4 components, this number of components will
    be encoded as [11], and not [100]

    It's really minor gains, but we're here to encode in the smallest amount of bits
    possible!

    These levels allows to have pretty big numbers for the elements. The third
    level (first decoded), can be at most 4 ('11'), so the second level can be at
    most 16 ('1111' : 4 bits), so the max number of circuits, components, inputs,
    and outputs is 65'536 ('1111111111111111' : 16 bits).

    It's a compromise: for some circuit libraries, some hardcoded bit lengths would
    save a few bits, but as the count of elements/ports go higher, it's a net gain.

    More details are in the methods themselves.

    The encoding is destructive: the components, inputs, and outputs are replaced by
    their indices these will become the new "names" during decoding. The order, which
    define functionality, is preserved.

    The main task is to define the wiring that connects the inputs, outputs,
    and components together. The core idea is not to define the wires themselves, but to
    define the connections. Each connection refers to a "provenance", meaning which
    circuit input or component output should the current port should be connected to.
    This is done using the indexes of these ports and components.
    """

    def __init__(self):
        super().__init__()

        self.library: CircuitDict = {}
        # [data ; bitlength]
        self.int_encoding: List[Tuple[int, int | Placeholder]] = []

        # Variables to keep count of the maximum number of components, inputs, and
        # outputs in the library. They will be in the global header.
        self.max_components = 0
        self.max_inputs = 0
        self.max_outputs = 0

    def encode(self, library: Schematics) -> bitarray:
        """
        Orchestrates the encoding process.
        """
        self.library = deepcopy(library.library)
        # See comment for 'max_*_bitlength' variables for explanation.
        self.circuits_bitlength: int = bitlength_with_offset(len(self.library))

        # Core encoding
        for circuit in self.library.values():
            if circuit.identifier == 0:
                continue
            self._encode_circuit(circuit)

        # Compute the number of bits necessary to encode the number of circuits,
        # maximum number of components, inputs and outputs necessary
        # (second level bit counting).
        # Offset because 0 component, input, or output is considered impossible.
        # For example, if we have a maximum number 'max_components' of 8 components:
        # - Here, during encoding:
        #     - '8' is encoded as '1000', so the number of bits to encode this maximum
        #       number would be 4.
        #     - But, with the offset, this max number becomes a "virtual" 7 that we can
        #       encode in 3 bits.
        #     - 'max_components_bitlength' is 3, we encode it in the global header.
        # - During decoding:
        #     - We decode '3' in the global header and deduce that 3 bits are enough
        #       to decode the number of component for each circuit.
        #     - For each local circuit header, we will decode the number of components
        #       by reading 3 bits.
        max_components_bitlength = bitlength_with_offset(self.max_components)
        max_inputs_bitlength = bitlength_with_offset(self.max_inputs)
        max_outputs_bitlength = bitlength_with_offset(self.max_outputs)

        # Here is the third level of bit counting. We do the same as the previous step,
        # but with the maximum number of all maximum bit lengths.
        # For example, if we have 9 circuits, 8 components maximum, 17 inputs maximum,
        # and 9 output maximum:
        # Here, during encoding.
        #   - There respective bit_length (as computed above), would be: 4, 3, 5, and 4.
        #   - 5 is the global maximum, we can encode it as 3 bits.
        #   - With the offset, we have a "virtual" 4 bits, which can be encoded in 3
        #     bits (no change).
        #   - 'max_bitlength' is 3, we encode it in the global header prelude.
        # During decoding:
        #   - We decode '3' in the global header prelude, and deduce that 3 bits are
        #     enough to decode the number of circuits, and maximum number of components,
        #     inputs, and outputs.
        #   - For each of these elements, we will decode them by reading 3 bits.
        max_bitlength = max(
            self.circuits_bitlength,
            max_components_bitlength,
            max_inputs_bitlength,
            max_outputs_bitlength,
        )
        core_bitlength = bitlength_with_offset(max_bitlength)

        bit_encoding = bitarray()

        # Global Header
        # Now, we will encode these previous numbers. But there's a new twist: these
        # encoding are also offset by one, as a bit size of '0' makes no sense.
        # So, if we keep the previous example:
        # Here, during encoding:
        #   - We want to encode 'bits_max', which is 3. With the offset,
        #     it will be '10' and not '11'. It's encoded in 2 bits, hardcoded.
        #   - To encode the other elements, we use the maximum number of bits. For the
        #     max number of components 8, we want to encode the bit length '3'
        #     (see above), which will be encoded as '010' (and not '011'). Note
        #     that this number is encoded in 3 bits: the 'bits_max' value.
        # During decoding:
        #   - We will read 2 bits: '10' = 2. We deduce that the number of bits
        #     to decode the rest of the header is 2 + 1 = 3, with the offset.
        #   - For the number of components, we will read 3 bits: '010' = 2. We
        #     deduce number of bits to read to decode the number of components
        #     will be 2 + 1 = 3, with the offset.
        #   - For the circuit with the maximum of 8 components, we will read the
        #     3 bits '111' = 7 + 1 = 8, with the offset. It's all coming together!
        bit_encoding.extend(int2bitlist_with_offset(core_bitlength, 2))
        bit_encoding.extend(
            int2bitlist_with_offset(self.circuits_bitlength, core_bitlength)
        )
        bit_encoding.extend(
            int2bitlist_with_offset(max_components_bitlength, core_bitlength)
        )
        bit_encoding.extend(
            int2bitlist_with_offset(max_inputs_bitlength, core_bitlength)
        )
        bit_encoding.extend(
            int2bitlist_with_offset(max_outputs_bitlength, core_bitlength)
        )

        # Finally encode the data. The raw encoding contains the integers values to
        # encode into bits, and the bit length if it was known, or a placeholder
        # that is now defined.
        for data, bitlength in self.int_encoding:
            match bitlength:
                case Placeholder.COMPONENTS:
                    bit_encoding.extend(
                        int2bitlist_with_offset(data, max_components_bitlength)
                    )
                case Placeholder.INPUTS:
                    bit_encoding.extend(
                        int2bitlist_with_offset(data, max_inputs_bitlength)
                    )
                case Placeholder.OUTPUTS:
                    bit_encoding.extend(
                        int2bitlist_with_offset(data, max_outputs_bitlength)
                    )
                case int():
                    bit_encoding.extend(int2bitlist(data, bitlength))
                case _:
                    raise ValueError("Unknown bitlength type.")

        return bit_encoding

    def _encode_circuit(self, circuit: Circuit):
        """
        circuit = [header, components, outputs]
        """
        metadata = self._encode_header(circuit)
        self._encode_components(circuit, metadata)
        self._encode_outputs(circuit, metadata)

    def _encode_header(self, circuit: Circuit) -> EncodedCircuitMetadata:
        """
        header = [n_components, n_inputs, n_outputs]
        n_components is used in decoding to know how many components to read
        n_inputs is used in decoding for safety check
        n_outputs is used in decoding to know how many outputs to read
        """
        # The metadata used during encoding : the bitlength in which to encode
        # the different elements.
        metadata = EncodedCircuitMetadata()

        # We "stash" the encoding: the number of components (with offset), will
        # be encoded in a number of bits deduced by the global maximum.
        self.int_encoding.append((len(circuit.components), Placeholder.COMPONENTS))
        # Update the global maximum.
        self.max_components = max(self.max_components, len(circuit.components))
        # Compute how many bits are necessary to encode the index of components.
        metadata.components_bitlength = bitlength_with_offset(len(circuit.components))

        self.int_encoding.append((len(circuit.inputs), Placeholder.INPUTS))
        self.max_inputs = max(self.max_inputs, len(circuit.inputs))
        metadata.inputs_bitlength = bitlength_with_offset(len(circuit.inputs))

        self.int_encoding.append((len(circuit.outputs), Placeholder.OUTPUTS))
        self.max_outputs = max(self.max_outputs, len(circuit.outputs))
        metadata.outputs_bitlength = bitlength_with_offset(len(circuit.outputs))

        return metadata

    def _encode_components(self, circuit: Circuit, metadata: EncodedCircuitMetadata):
        """
        components = [component_0, component_1, ..., component_n]
        """
        for component in circuit.components.values():
            self._encode_component(component, circuit, metadata)

    def _encode_component(
        self, component: Circuit, circuit: Circuit, metadata: EncodedCircuitMetadata
    ):
        """
        component = [circuit_id, inputs]

        During encoding, the full id of the circuit is lost. But its index in the
        library is unique, and that's what we encode.
        During decoding, this index will be the new id.
        """
        circuit_ids = list(self.library.keys())

        self.int_encoding.append(
            (circuit_ids.index(component.identifier), self.circuits_bitlength)
        )

        self._encode_inputs(component, circuit, metadata)

    def _encode_inputs(
        self, component: Circuit, circuit: Circuit, metadata: EncodedCircuitMetadata
    ):
        """
        inputs = [input_0, input_1, ..., input_n]
        input = [provenance, location]

        provenance = 0 if the input is a circuit input, 1 if it is a component output
        location =
            if provenance = 0:
                location = index in the circuit inputs
            if provenance = 1:
                location = wiring (see _encode_component_wiring())

        'provenance' is an optimization trick. It allows for a specific input source
        (circuit input or component output) to be referred in only one bit. It works
        empirically if we consider that usually the number of inputs is greater than the
        number of input of any of its component.

        Note that there's a dual of provenance for the output, where we would encode the
        wiring "in reverse", starting from the outputs. This method will save bits only
        if the number of outputs is greater than the number of inputs, like for the
        nand2tetris CPU (but not for the ALU).
        """
        circuit_input = [wire.id for wire in circuit.inputs.values()]

        for input in component.inputs.values():
            if input.id in circuit_input:
                self.int_encoding.append((0, 1))
                self.int_encoding.append(
                    (circuit_input.index(input.id), metadata.inputs_bitlength)
                )
            else:
                self.int_encoding.append((1, 1))
                self._encode_component_wiring(input, circuit.components, metadata)

    def _encode_outputs(self, circuit: Circuit, metadata: EncodedCircuitMetadata):
        """
        outputs = [output_0, output_1, ..., output_n]
        output = wiring (see _encode_component_wiring())
        """
        for output in circuit.outputs.values():
            self._encode_component_wiring(output, circuit.components, metadata)

    def _encode_component_wiring(
        self, wire: Wire, components: CircuitDict, metadata: EncodedCircuitMetadata
    ):
        """
        wiring = [component_idx, output_idx]
        component_idx is the index of source component within the current circuit.
        output_idx is the index of the output in the component pin on that source
        component.
        """
        for idx, sub_component in enumerate(components.values()):
            outputs = [wire.id for wire in sub_component.outputs.values()]
            if wire.id in outputs:
                self.int_encoding.append((idx, metadata.components_bitlength))
                self.int_encoding.append(
                    (outputs.index(wire.id), metadata.outputs_bitlength)
                )
                return
        raise ValueError(f"Wire {wire.id} not found in any sub_component outputs")
