from schematics import SchematicsBuilder, get_schematic_idx
from encoding import CircuitEncoder
from decoding import CircuitDecoder


def main():
    builder = SchematicsBuilder()
    builder.build_circuits()
    schematics = builder.schematics

    print(str(get_schematic_idx(9, schematics)))

    # print(schematics)

    # partial = deepcopy(schematics)
    # while len(partial) > 9:
    #     partial.popitem()

    encoder = CircuitEncoder(schematics)
    encoded = encoder.encode()
    print(encoded)

    decoder = CircuitDecoder(encoded)
    decoded = decoder.decode()
    # print(decoded)

    round_trip = CircuitEncoder(decoded).encode()

    print(encoded)
    for idx, (a, b) in enumerate(zip(encoded, round_trip)):
        if a != b:
            print(f"Index {idx} is different: {a} != {b}")

    print(len(round_trip))
    assert encoded == round_trip

    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB


if __name__ == "__main__":
    main()
