from copy import deepcopy
from typing import List, Literal, Tuple

from bitarray import bitarray

from nand.bits_utils import bitlength, int2bitlist
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
    to encode *the number of bit necessary* for the count of components, inputs, and
    outputs for the circuits.

    Finally, there's a third level of bit counting, to know how many bits are necessary
    to encode the number of bits above. It's two bit long.

    These last two levels are encoded in a global header.

    There indirections allow with very few bits to encode a huge set.

    Please note that there's always an offset of 1: 0 component, input, or output
    is considered impossible. So a '00' encoded should be decoded as 1, '1' as 2,
    '10' as 3, etc.

    For example, with the third level of bit counting being 3 :
        - It means that 3 bits are necessary for the second level.
        - So, the second level is encoded in 3 bits. The range available at this level
        is [1, (1 << 3) + 1] = [1, 8].
        - So, the number of components, inputs and outputs, can be encoded in a maximum
        of 8 bits. The range available for them [1, 256], which seems to me already
        overkill for big circuits.

    An example of global header

    The encoding is destructive: the components, inputs, and outputs are replaced by
    their indices these will become the new "names" during decoding. The order, which
    preserves functionality, is preserved.

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

        # TODO : update and fix this docstring

        1.  Performs a "dry run" of the encoding to gather statistics about the
            circuits, such as the maximum number of components, inputs, and outputs.
        2.  Calculates the necessary bit widths for various fields based on these stats.
        3.  Constructs a global header with these bit widths.
        4.  Encodes the circuits one by one into a final bitarray.

        Note: The NAND gate (ID 0) is considered a primitive and is not encoded.
        """
        self.library: CircuitDict = deepcopy(library.library)
        self.encoding: List[
            Tuple[
                int,
                int | Literal["COMPONENTS"] | Literal["INPUTS"] | Literal["OUTPUTS"],
            ]
        ] = []

        self.max_components = 0
        self.max_inputs = 0
        self.max_outputs = 0
        # -1 for nand, -1 because a library of 0 circuit is silly.
        self.bit_circuits = bitlength(len(self.library) - 1 - 1)

        for circuit in self.library.values():
            if circuit.identifier == 0:
                continue
            self._encode_circuit(circuit)

        bit_components = bitlength(self.max_components - 1)
        bit_inputs = bitlength(self.max_inputs - 1)
        bit_outputs = bitlength(self.max_outputs - 1)

        max_of_all_max = max(bit_components, bit_inputs, bit_outputs, self.bit_circuits)
        bits_max = bitlength(max_of_all_max)

        bit_encoding = bitarray()

        # Global Header
        # The first 2 bits define the size of the fields that define the size of
        # the data
        bit_encoding.extend(int2bitlist(bits_max, 2))
        # The size of the circuit identifiers
        bit_encoding.extend(int2bitlist(self.bit_circuits, bits_max))
        # The size of the component counts
        bit_encoding.extend(int2bitlist(bit_components, bits_max))
        # The size of the input counts
        bit_encoding.extend(int2bitlist(bit_inputs, bits_max))
        # The size of the output counts
        bit_encoding.extend(int2bitlist(bit_outputs, bits_max))

        for i, lit in self.encoding:
            if lit == "COMPONENTS":
                bit_encoding.extend(int2bitlist(i, bit_components))
            elif lit == "INPUTS":
                bit_encoding.extend(int2bitlist(i, bit_inputs))
            elif lit == "OUTPUTS":
                bit_encoding.extend(int2bitlist(i, bit_outputs))
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
        Updates the maximums found so far.
        We store n-1 values to save space: we assume there is at least one component,
        one input, and one output in each circuit.
        """

        self.encoding.append((len(circuit.components) - 1, "COMPONENTS"))
        self.max_components = max(self.max_components, len(circuit.components))
        self.bit_components = bitlength(len(circuit.components) - 1)

        self.encoding.append((len(circuit.inputs) - 1, "INPUTS"))
        self.max_inputs = max(self.max_inputs, len(circuit.inputs))
        self.bit_inputs = bitlength(len(circuit.inputs) - 1)

        self.encoding.append((len(circuit.outputs) - 1, "OUTPUTS"))
        self.max_outputs = max(self.max_outputs, len(circuit.outputs))
        self.bit_outputs = bitlength(len(circuit.outputs) - 1)

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
            (circuit_ids.index(component.identifier), self.bit_circuits)
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
                self.encoding.append((circuit_input.index(input.id), self.bit_inputs))
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
                self.encoding.append((idx, self.bit_components))
                self.encoding.append((outputs.index(wire.id), self.bit_outputs))
                return
        raise ValueError(f"Wire {wire.id} not found in any sub_component outputs")
