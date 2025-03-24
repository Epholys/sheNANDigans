from schematics import SchematicsBuilder
from simulator_fast import SimulatorFast
from simulator_debug import SimulatorDebug


def main():
    # builder = SchematicsBuilder()
    # builder.build_circuits()
    # reference_circuits = builder.schematics
    #
    # encoded = CircuitEncoder(reference_circuits).encode()
    # round_trip_circuits = CircuitDecoder(encoded).decode()
    #
    builder = SchematicsBuilder()
    builder.build_circuits()
    library = builder.schematics
    c = library.get_schematic_idx(2)

    print(c)

    fast = SimulatorFast(c)
    print(fast)
    print(c)

    fast.simulate([True, False, True])
    print(fast)
    print(c)

    debug = SimulatorDebug(c)
    print(debug)
    print(c)

    debug.simulate([True, False, True])
    print(debug)
    print(c)

    # circuit = get_schematic_idx(10, schematics)
    # wires = [wire for wire in circuit.inputs.values()]
    # for wire in wires:
    #     wire.state = True
    # success = circuit.simulate()
    # if not success:
    #     print("simulation failed!")
    #     print(circuit)
    #     return

    # perfs = circuit.sum_performance()
    # print(f"performance data:\n{perfs}")
    # print(
    #     f"failure percentage = {100 * perfs.simulation_failure / (perfs.simulation_failure + perfs.simulation_success)}%"
    # )

    # print(schematics)

    # encoder = CircuitEncoder(schematics)
    # encoded = encoder.encode()
    # print(encoded)

    # decoder = CircuitDecoder(encoded)
    # decoded = decoder.decode()
    # # print(decoded)

    # round_trip = CircuitEncoder(decoded).encode()

    # print(encoded)
    # for idx, (a, b) in enumerate(zip(encoded, round_trip):
    #     if a != b:
    #         print(f"Index {idx} is different: {a} != {b}")

    # print(len(round_trip)
    # assert encoded == round_trip

    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB


if __name__ == "__main__":
    main()
