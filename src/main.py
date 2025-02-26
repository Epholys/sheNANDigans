from copy import deepcopy
from schematics import SchematicsBuilder
from encoding import CircuitEncoder
from decoding import CircuitDecoder

def main():
    builder = SchematicsBuilder()
    builder.build_circuits()
    schematics = builder.schematics

    partial = deepcopy(schematics)
    while len(partial) > 9:
        partial.popitem()

    encoder = CircuitEncoder(partial)
    encoded = encoder.encode()
    print(encoded)

    decoder = CircuitDecoder(encoded.copy())
    decoded = decoder.decode()
    # print(decoded)

    round_trip = CircuitEncoder(decoded).encode()
    print(round_trip)

    print(len(round_trip))

    assert(encoded == round_trip)

    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
    # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB

if __name__ == "__main__":
    main()