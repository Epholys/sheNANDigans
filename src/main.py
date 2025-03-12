from schematics import SchematicsBuilder, get_schematic_idx
from encoding import CircuitEncoder
from decoding import CircuitDecoder


def main():
    builder = SchematicsBuilder()
    builder.build_circuits()
    schematics = builder.schematics

    circuit = get_schematic_idx(10, schematics)
    circuit.reset()
    wires = [wire for wire in circuit.inputs.values()]
    for wire in wires:
        wire.state = True
    success = circuit.simulate()
    if not success:
        print("simulation failed!")
        print(repr(circuit))
        return

    perfs = circuit.sum_performance()
    print(f"performance data:\n{perfs}")
    print(
        f"failure percentage = {100 * perfs.simulation_failure / (perfs.simulation_failure + perfs.simulation_success)}"
    )

    # print(schematics)

    # partial = deepcopy(schematics)
    # while len(partial) > 9:
    #     partial.popitem()

    # encoder = CircuitEncoder(schematics)
    # encoded = encoder.encode()
    # print(encoded)

    # decoder = CircuitDecoder(encoded)
    # decoded = decoder.decode()
    # print(decoded)

    # round_trip = CircuitEncoder(decoded).encode()

    # print(encoded)
    # for idx, (a, b) in enumerate(zip(encoded, round_trip)):
    #     if a != b:
    #         print(f"Index {idx} is different: {a} != {b}")

    # print(len(round_trip))
    # assert encoded == round_trip

    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB


if __name__ == "__main__":
    main()
