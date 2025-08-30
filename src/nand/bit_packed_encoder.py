from copy import deepcopy
from typing import List, Literal, Tuple

from bitarray import bitarray

from nand.bits_utils import bitlength_with_offset, int2bitlist, int2bitlist_with_offset
from nand.circuit import Circuit, CircuitDict, Wire
from nand.circuit_encoder import CircuitEncoder
from nand.schematics import Schematics


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
    to encode the number of bits above. It's two bit long.

    These last two levels are encoded in a global header.

    Note that there's an offset of 1 each time a value of '0' does not make any sense
    For example, 0 component, input, or output for a circuit is considered impossible.
    So, if we have a circuit with 4 components, this number of components will be
    encoded as [11], and not [100]
    Or, if we have 16 inputs maximum for the library, the bit length saved for the
    second level will be [1111] and not [10000].

    It's really minor gains, but we're here to encode in the smallest amount of bits
    possible!

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

    def encode(self, library: Schematics) -> bitarray:
        """
        Orchestrates the encoding process.
        """
        self.library: CircuitDict = deepcopy(library.library)
        self.encoding: List[
            Tuple[
                int,
                int | Literal["COMPONENTS"] | Literal["INPUTS"] | Literal["OUTPUTS"],
            ]
        ] = []

        # Variables to keep count of the maximum number of components, inputs, and
        # outputs in the library. They will be in the global header.
        self.max_components = 0
        self.max_inputs = 0
        self.max_outputs = 0

        # See below for explanation.
        self.circuits_bitlength: int = bitlength_with_offset(len(self.library))

        # Core encoding
        for circuit in self.library.values():
            if circuit.identifier == 0:
                continue
            self._encode_circuit(circuit)

        # Compute the number of bits necessary to encode the number of circuits,
        # maximum number of components, inputs and outputs necessary
        # (second level indirection).
        # Offset because 0 component, input, or output is considered impossible.
        # For example, if we have a maximum number 'max_components' of 8 components:
        # - Here, during encoding:
        #     - '8' is encoded as '1000', so the number of bits to encode this maximum
        #       number would be 4.
        #     - But, with the offset, this max number becomes a "virtual" 7 that we can
        #       encode in 3 bits.
        #     - 'bit_components' is 3, we encode it in the global header.
        # - During decoding:
        #     - We decode '3' in the global header, and deduce that 3 bits are enough
        #       to decode the number of component for each circuit.
        #     - For each local circuit header, we will decode the number of components
        #       by reading 3 bits.
        max_components_bitlength = bitlength_with_offset(self.max_components)
        max_inputs_bitlength = bitlength_with_offset(self.max_inputs)
        max_outputs_bitlength = bitlength_with_offset(self.max_outputs)

        # Here is the third level of indirection. We do the same as the previous step,
        # but with the maximum number of all the maximum numbers.
        # For example, if we have 9 circuits, 8 components maximum, 17 inputs maximum,
        # and 9 output maximum:
        # Here, during encoding.
        #   - There respective bit_length (as computed above), would be: 4, 3, 5, and 4.
        #   - 5 is the global maximum, we can encode it as 3 bits.
        #   - With the offset, we have a "virtual" 4 bits, which can be encoded in 3
        #     bits (no change).
        #   - 'bits_max' is 3, we encode it in the global header prelude.
        # During decoding:
        #   - We decode '3' in the global header prelude, and deduce that 3 bits are
        #     enough to decode the number of circuits, and maximum number of components,
        #     inputs, and outputs.
        #   - For each of these elements, we will decode them by reading 3 bits.
        # **Important note**: the number of circuit does not have 3 levels, only 2.
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
        # These indirections allows to have quite a big range. At the 3rd level,
        # the maximum is '11', so 3 + 1 = 4 bits. So, at the 2nd level, we have
        # a maximum of '1111', which is 15 + 1 = 16. And, at the 1st level, for
        # the maximum number of components, inputs, and outputs: 2 ** 16 (65'536). TODO ????????
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

        for i, lit in self.encoding:
            if lit == "COMPONENTS":
                bit_encoding.extend(int2bitlist(i, max_components_bitlength))
            elif lit == "INPUTS":
                bit_encoding.extend(int2bitlist(i, max_inputs_bitlength))
            elif lit == "OUTPUTS":
                bit_encoding.extend(int2bitlist(i, max_outputs_bitlength))
            else:
                bit_encoding.extend(int2bitlist(i, lit))

        return bit_encoding

    def _encode_circuit(self, circuit: Circuit):
        """
        circuit = [header, components, outputs]
        """
        self._encode_header(circuit)
        self._encode_components(circuit)
        self._encode_outputs(circuit)

    def _encode_header(self, circuit: Circuit):
        """
        header = [n_components, n_inputs, n_outputs]
        n_components is used in decoding to know how many components to read
        n_inputs is used in decoding for safety check
        n_outputs is used in decoding to know how many outputs to read
        """
        # We "stash" the encoding: the number of components (with offset), will
        # be encoded in a number of bits deduced by the global maximum
        # (see comment above)
        self.encoding.append((len(circuit.components) - 1, "COMPONENTS"))
        # Update the global maximum.
        self.max_components = max(self.max_components, len(circuit.components))
        # Compute how many bits are necessary to encode the index of components.
        self.components_bitlength = bitlength_with_offset(len(circuit.components))

        self.encoding.append((len(circuit.inputs) - 1, "INPUTS"))
        self.max_inputs = max(self.max_inputs, len(circuit.inputs))
        self.inputs_bitlength = bitlength_with_offset(len(circuit.inputs))

        self.encoding.append((len(circuit.outputs) - 1, "OUTPUTS"))
        self.max_outputs = max(self.max_outputs, len(circuit.outputs))
        self.outputs_bitlength = bitlength_with_offset(len(circuit.outputs))

    def _encode_components(self, circuit: Circuit):
        """
        components = [component_0, component_1, ..., component_n]
        """
        for component in circuit.components.values():
            self._encode_component(component, circuit)

    def _encode_component(self, component: Circuit, circuit: Circuit):
        """
        component = [id, inputs]
        id is not the identifier of the circuit, but the index of the component in the
        circuit.
        # TODO explain this better
        But, during decoding this index becomes the identifier of the component.
        """
        circuit_ids = list(self.library.keys())
        self.encoding.append(
            (circuit_ids.index(component.identifier), self.circuits_bitlength)
        )

        self._encode_inputs(component, circuit)

    def _encode_inputs(self, component: Circuit, circuit: Circuit):
        """
        inputs = [input_0, input_1, ..., input_n]
        input = [provenance, location]

        provenance = 0 if the input is a circuit input, 1 if it is a component output
        location =
            if provenance = 0:
                location = index in the circuit inputs
            if provenance = 1:
                location = wiring (see _encode_component_wiring())
        """
        circuit_input = [wire.id for wire in circuit.inputs.values()]

        for input in component.inputs.values():
            if input.id in circuit_input:
                self.encoding.append((0, 1))
                self.encoding.append(
                    (circuit_input.index(input.id), self.inputs_bitlength)
                )
            else:
                self.encoding.append((1, 1))
                self._encode_component_wiring(input, circuit.components)

    def _encode_outputs(self, circuit: Circuit):
        """
        outputs = [output_0, output_1, ..., output_n]
        output = wiring (see _encode_component_wiring())
        """
        for output in circuit.outputs.values():
            self._encode_component_wiring(output, circuit.components)

    def _encode_component_wiring(self, wire: Wire, components: CircuitDict):
        """
        wiring = [component_idx, output_idx]
        component_idx is the index of source component within the current circuit.
        output_idx is the index of the output in the component pin on that source
        component.
        """
        for idx, sub_component in enumerate(components.values()):
            outputs = [wire.id for wire in sub_component.outputs.values()]
            if wire.id in outputs:
                self.encoding.append((idx, self.components_bitlength))
                self.encoding.append((outputs.index(wire.id), self.outputs_bitlength))
                return
        raise ValueError(f"Wire {wire.id} not found in any sub_component outputs")
