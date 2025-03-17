import itertools
from schematics import SchematicsBuilder
from wire import WireExtendedState


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
    circuit = library.get_schematic_idx(2)

    print([x for x in itertools.product([circuit.identifier, "OR"], [False])])

    print(repr(circuit))
    print(str(circuit))

    circuit.inputs["A"].state = True
    circuit.inputs["B"].state = True

    circuit.simulate()

    print(
        f"{''.join(str(win) for win in circuit.inputs.values())} → {''.join(str(wout) for wout in circuit.outputs.values())}"
    )

    circuit.debug_mode()
    circuit.reset()
    print(repr(circuit))
    print(str(circuit))

    circuit.inputs["A"].state = WireExtendedState.UNKNOWN
    circuit.inputs["B"].state = WireExtendedState.OFF

    print(str(circuit))

    circuit.simulate()

    print(
        f"{''.join(str(win) for win in circuit.inputs.values())} → {''.join(str(wout) for wout in circuit.outputs.values())}"
    )

    print(circuit)

    # circuit = get_schematic_idx(10, schematics)
    # wires = [wire for wire in circuit.inputs.values()]
    # for wire in wires:
    #     wire.state = True
    # success = circuit.simulate()
    # if not success:
    #     print("simulation failed!")
    #     print(repr(circuit))
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
