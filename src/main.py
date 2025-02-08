from ast import Or
from base64 import encode
from copy import deepcopy
from schematics import schematics
from encoding import CircuitEncoder
from schematics import add_circuits

def main():
    add_circuits()
    only_not = deepcopy(schematics)
    while len(only_not) > 2:
        only_not.popitem()
    print(only_not)
    encoder = CircuitEncoder(only_not)
    print(encoder.encode())

    not_and = deepcopy(schematics)
    while len(not_and) > 3:
        not_and.popitem()
    print(not_and)
    encoder = CircuitEncoder(not_and)
    print(encoder.encode())

    not_and_or = deepcopy(schematics)
    while len(not_and_or) > 4:
        not_and_or.popitem()
    print(not_and_or)
    encoder = CircuitEncoder(not_and_or)
    print(encoder.encode())

    not_and_or_nor = deepcopy(schematics)
    while len(not_and_or_nor) > 5:
        not_and_or_nor.popitem()
    print(not_and_or_nor)
    encoder = CircuitEncoder(not_and_or_nor)
    print(encoder.encode())

    not_and_or_nor_xor = deepcopy(schematics)
    while len(not_and_or_nor_xor) > 6:
        not_and_or_nor_xor.popitem()
    print(not_and_or_nor_xor)
    encoder = CircuitEncoder(not_and_or_nor_xor)
    print(encoder.encode())

    encoder = CircuitEncoder(schematics)
    full_encoding = encoder.encode()
    print(full_encoding)

    nodebug_encoding = [x for x in full_encoding if isinstance(x,  int)]
    print(nodebug_encoding)
    print(len(nodebug_encoding))

    # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

if __name__ == "__main__":
    main()