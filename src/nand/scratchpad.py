from nand.bit_packed_decoder import BitPackedDecoder
from nand.bit_packed_encoder import BitPackedEncoder
from nand.schematics import SchematicsBuilder


builder = SchematicsBuilder()
builder.build_circuits()
schematics = builder.schematics
encoding = BitPackedEncoder().encode(schematics)
print(encoding.to01())
print(len(encoding.to01()))
dec = BitPackedDecoder()
lib = dec.decode(encoding)
# file = open("bpe.bin", mode="xb")
# file.write(encoding.tobytes())
