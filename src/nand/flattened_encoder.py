
from bitarray import bitarray

from nand.bit_packed_encoder import BitPackedEncoder, EncodedCircuitMetadata
from nand.bits_utils import bitlength_with_offset
from nand.circuit import Circuit, CircuitDict, Wire, CircuitId
from nand.circuit_builder import CircuitLibrary
from nand.flattener import flatten_circuit


class _FlattenedEncodedCircuitMetadata(EncodedCircuitMetadata):
    def __init__(self):
        super().__init__()
        self.zero_one_flag: bool = False
        self.rolling_nand_bitlength: int = 0
        self.nand_count: int = 0
        self.nand_idx_map: dict[CircuitId, int] = {}

class FlattenedEncoder(BitPackedEncoder):
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

    def encode(self, library: CircuitLibrary) -> bitarray:
        """
        Orchestrates the encoding process.
        """
        flattened_library = CircuitLibrary()
        for _, circuit in library.get_all_circuits().items():
            flattened_library.add_circuit(flatten_circuit(circuit))

        return super().encode(library)

    def _encode_circuit(self, circuit: Circuit):
        """
        circuit = [header, components, outputs]
        """
        print()
        print(f"encode circuit of name {circuit.name}")
        metadata = self._encode_header(circuit)
        self._encode_nands(circuit, metadata)
        self._encode_nand_outputs(circuit, metadata)

    def _encode_header(self, circuit: Circuit) -> _FlattenedEncodedCircuitMetadata:
        """
        header = [zero_one_flag, n_components, n_inputs, n_outputs]
        zero_one_flag is used to know if the circuit use the ZERO or ONE core gate.
        n_components is used in decoding to know how many components to read
        n_inputs is used in decoding for safety check
        n_outputs is used in decoding to know how many outputs to read
        """
        # The metadata used during encoding : the bitlength in which to encode
        # the different elements.
        metadata = _FlattenedEncodedCircuitMetadata()

        ids = [circuit.identifier for circuit in circuit.components.values()]
        metadata.zero_one_flag = any([id_ == 1 or id_ == 2 for id_ in ids])
        print(f"zero on flag = {0 if not metadata.zero_one_flag else 1}")
        self.int_encoding.append((0 if not metadata.zero_one_flag else 1, 1))

        parent_metadata = super()._encode_header(circuit)
        metadata.components_bitlength = 0
        metadata.inputs_bitlength = parent_metadata.inputs_bitlength
        metadata.outputs_bitlength = parent_metadata.outputs_bitlength

        return metadata

    def _encode_nands(self, circuit: Circuit, metadata: _FlattenedEncodedCircuitMetadata):
        """
        nands = [nand_0, nand_1, ..., nand_n]
        """
        for nand in circuit.components.values():
            self._encode_nand_inputs(nand, circuit, metadata)

    def _encode_nand_inputs(
        self, nand: Circuit, circuit: Circuit, metadata: _FlattenedEncodedCircuitMetadata
    ):
        """
        inputs = [input_0, input_1, ..., input_n]
        input = [provenance, location]

        if zero_one_flag is *not* set:
            provenance = 0 if the input is a circuit input, 1 if it is a component output
            location =
                if provenance = 0:
                    location = index in the circuit inputs
                if provenance = 1:
                    location = wiring (see _encode_component_wiring())
        else:
            provenance = 00 if the input is a circuit input
            provenance = 010 if the input is a ZERO gate
            provenance = 011 of the inputs is a ONE gate
            location =
                if provenance = 00:
                    location = index in the circuit inputs
                if provenance = 010 or provenance = 011:
                    location isn't encoded
                if provenance = 1:
                    location = wiring (see _encode_component_wiring())
        """
        circuit_input = [wire.id for wire in circuit.inputs.values()]

        for wire in nand.inputs.values():
            if wire.id in circuit_input:
                if not metadata.zero_one_flag:
                    print("not zero one : encode input provenance as 0")
                    self.int_encoding.append((0, 1))
                else:
                    print("zero one : encode input provenance as 00")
                    self.int_encoding.append((0, 1)) # TODO one line ?
                    self.int_encoding.append((0, 1))
                print(f"input encoding : input index : {circuit_input.index(wire.id)} , input_bl = {metadata.inputs_bitlength}")
                self.int_encoding.append(
                    (circuit_input.index(wire.id), metadata.inputs_bitlength)
                )
            else:
                # The provenance encoding is set in the method below
                self._encode_nand_wiring(wire, circuit.components, metadata)

    def _encode_nand_outputs(self, circuit: Circuit, metadata: _FlattenedEncodedCircuitMetadata):
        """
        outputs = [output_0, output_1, ..., output_n]
        output = 
        """
        print("--- nand output ---")
        for circuit_output in circuit.outputs.values():
            #print(f"circuit output: {circuit_output.id}")
            for key, component in circuit.components.items():
                #print(f"try component key : {key}")
                outputs = [wire.id for wire in component.outputs.values()]  # [0] ?
                #print(f"component outputs : {outputs}")
                if circuit_output.id in outputs:
                    _update(key, metadata)

                    print(f"output: nand of idx {metadata.nand_idx_map[key]} (in {metadata.rolling_nand_bitlength} bits)")
                    self.int_encoding.append((metadata.nand_idx_map[key], metadata.rolling_nand_bitlength))
                    return

    def _encode_nand_wiring(
        self, wire: Wire, circuit_components: CircuitDict, metadata: _FlattenedEncodedCircuitMetadata
    ):
        """
        wiring = [component_idx]

        component_idx is
        """
        print("--- nand wiring ---")
        for key, component in circuit_components.items():
            outputs = [wire.id for wire in component.outputs.values()]  # [0] ?
            if wire.id in outputs:
                if metadata.zero_one_flag:
                    print("zero one flag")
                    if component.identifier == 1:
                        print("ZERO : encode as 010")
                        self.int_encoding.append((0, 1))  # TODO one line ?
                        self.int_encoding.append((1, 1))
                        self.int_encoding.append((0, 1))
                        return
                    elif component.identifier == 2:
                        print("ONE : encode as 011")
                        self.int_encoding.append((0, 1))  # TODO one line ?
                        self.int_encoding.append((1, 1))
                        self.int_encoding.append((1, 1))
                        return
                    elif component.identifier != 0:
                        raise ValueError("Non-nand circuit present in FlattenedEncoder")

                print("NAND : encode provenance as 1")
                self.int_encoding.append((1, 1))

                _update(key, metadata)

                print(f"encoding append nand wiring : {metadata.nand_idx_map[key]} (in {metadata.rolling_nand_bitlength} bits)")
                self.int_encoding.append(
                    (metadata.nand_idx_map[key], metadata.rolling_nand_bitlength)
                )
                return
        raise ValueError(f"Wire {wire.id} not found in any component outputs")


def _update(nand_component_id: CircuitId, metadata: _FlattenedEncodedCircuitMetadata):
    print("- update -")
    if nand_component_id not in metadata.nand_idx_map:
        print(f"key {nand_component_id} not in map ; SET nand idx map [key] as {metadata.nand_count}")
        metadata.nand_idx_map[nand_component_id] = metadata.nand_count
        print("increment nand_count")
        metadata.nand_count += 1
        print(
            f"compute nand count bl (w/ offset) : for {metadata.nand_count} bl is {bitlength_with_offset(metadata.nand_count)}"
        )
        bl = bitlength_with_offset(metadata.nand_count)
        if bl > metadata.rolling_nand_bitlength:
            print(f"nand count bl > rolling_nand_bl ({metadata.rolling_nand_bitlength}), set")
            metadata.rolling_nand_bitlength = bl
    print("- -")