from nand.bit_packed_decoder import BitPackedDecoder
from nand.bit_packed_encoder import BitPackedEncoder
from nand.circuit import Circuit
from nand.circuit_library import CircuitLibrary
from nand.graph_flattened import GraphOptions, save_graph
from nand.graph_nested import generate_graph
from nand.nand2tetris_hack_alu import HackALUBuilder
from nand.optimization_level import OptimizationLevel
from nand.playground_circuit_builder import PlaygroundCircuitBuilder
from nand.rolling_decoder import RollingDecoder
from nand.rolling_encoder import RollingEncoder
from nand.simulator_builder import build_fasts, build_simulator
from tests.test_playground_schematics import TestPlaygroundLibrary

play_builder = PlaygroundCircuitBuilder()
play_builder.build_circuits()
library = play_builder.library

enc = RollingEncoder()
b = enc.encode(library)
dec = RollingDecoder().decode(b)

tests= TestPlaygroundLibrary()
circuit = dec.get_circuit_from_idx(10)
sims = build_fasts(circuit)
print(len(sims))
for sim in sims:
    s = [None] * 10 + [sim]
    tests.test_2bits_adder(s)

exit()

# flattened_builder = FlattenedHackALUBuilder()
# flattened_builder.build_circuits()
# flattened_library = flattened_builder.library
# 
# print(flattened_library.get_circuit_from_idx(25))
# print(len(flattened_library.get_circuit_from_idx(25).components))

small_lib: CircuitLibrary = CircuitLibrary()
for i in [0, 1, 2, 3, 4, 5, 7, 8, 9]:
    small_lib.add_circuit(library.get_circuit_from_idx(i))

encoder: RollingEncoder  = RollingEncoder()
b = encoder.encode(small_lib)

print("---")
print(b.to01())
print("---")

decoder = RollingDecoder()
decoder.decode(b)



#
# compare_encoders([BitPackedEncoder(), RollingEncoder()], [(library, "")])

exit()

play_builder = PlaygroundCircuitBuilder()
play_builder.build_circuits()
library = play_builder.library


def build_half_adder(library):
    half_adder = Circuit("Half-Adder")

    half_adder.add_component("XOR", library.get_circuit("XOR"))  # Previously defined
    half_adder.add_component("AND", library.get_circuit("AND"))

    half_adder.connect_input("A", "XOR", "A")
    half_adder.connect_input("B", "XOR", "B")
    half_adder.connect_input("A", "AND", "A")
    half_adder.connect_input("B", "AND", "B")

    half_adder.connect_output("AND", "OUT", "CARRY")
    half_adder.connect_output("XOR", "OUT", "SUM")

    return half_adder


half_adder = build_half_adder(library)

debug = build_simulator(half_adder, OptimizationLevel.FAST)  # Automatically optimized
result = debug.simulate([True, False])
assert result == [False, True]  # 1 + 0 = 01

play_builder = HackALUBuilder()
play_builder.build_circuits()
library = play_builder.library

reference_encoding = BitPackedEncoder().encode(library)
round_trip_library = BitPackedDecoder().decode(reference_encoding)
round_trip_encoding = BitPackedEncoder().encode(round_trip_library)

assert reference_encoding == round_trip_encoding

graph = generate_graph(
    half_adder, GraphOptions(is_compact=True, is_aligned=True, bold_io=True)
)
save_graph(graph, "half_adder", "svg")
