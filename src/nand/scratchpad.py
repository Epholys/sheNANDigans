from nand.bit_packed_decoder import BitPackedDecoder
from nand.bit_packed_encoder import BitPackedEncoder
from nand.schematics import SchematicsBuilder

builder = SchematicsBuilder()
builder.build_circuits()
schematics = builder.schematics
nor = schematics.get_schematic_idx(4)
print(nor)
print(repr(nor))
# file = open("bpe.bin", mode="xb")
# file.write(encoding.tobytes())
