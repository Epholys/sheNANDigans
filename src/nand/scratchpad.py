from nand.circuit import Circuit
from nand.default_decoder import DefaultDecoder
from nand.default_encoder import DefaultEncoder
from nand.graph_nested import GraphOptions, generate_graph, save_graph
from nand.optimization_level import OptimizationLevel
from nand.playground_circuit_builder import PlaygroundCircuitBuilder
from nand.simulator_builder import build_simulator

builder = PlaygroundCircuitBuilder()
builder.build_circuits()
library = builder.library


def build_half_adder(library):
    half_adder = Circuit("Half-Adder")

    half_adder.add_component("XOR", library.get_circuit("XOR"))  # Previously defined
    half_adder.add_component("AND", library.get_circuit("AND"))

    half_adder.connect_input("A", "XOR", "A")
    half_adder.connect_input("B", "XOR", "B")
    half_adder.connect_input("A", "AND", "A")
    half_adder.connect_input("B", "AND", "B")

    half_adder.connect_output("CARRY", "AND", "OUT")
    half_adder.connect_output("SUM", "XOR", "OUT")

    return half_adder


half_adder = build_half_adder(library)
simulator = build_simulator(
    half_adder, OptimizationLevel.FAST
)  # Automatically optimized
result = simulator.simulate([True, False])
assert result == [False, True]  # 1 + 0 = 01

builder = PlaygroundCircuitBuilder()
builder.build_circuits()
library = builder.library

reference_encoding = DefaultEncoder().encode(library)
round_trip_library = DefaultDecoder().decode(reference_encoding)
round_trip_encoding = DefaultEncoder().encode(round_trip_library)

assert reference_encoding == round_trip_encoding

graph = generate_graph(
    half_adder, GraphOptions(is_compact=True, is_aligned=True, bold_io=True)
)
save_graph(graph, "half_adder", "svg")
