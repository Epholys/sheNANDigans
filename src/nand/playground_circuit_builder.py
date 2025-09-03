from nand.circuit import Circuit
from nand.circuit_builder import CircuitBuilder


class PlaygroundCircuitBuilder(CircuitBuilder):
    def __init__(self):
        super().__init__()

    def build_circuits(self):
        super().build_circuits()
        self.add_not()
        self.add_and()
        self.add_or()
        self.add_nor()
        self.add_xor()
        self.add_half_adder()
        self.add_full_adder()
        self.add_2bits_adder()
        self.add_4bits_adder()
        self.add_8bits_adder()
        return self.library

    def add_not(self):
        not_gate = Circuit("NOT")
        not_gate.add_component("NAND", self.library.get_circuit(0))
        not_gate.connect_input("IN", "NAND", "A")
        not_gate.connect_input("IN", "NAND", "B")
        not_gate.connect_output("OUT", "NAND", "OUT")
        self.library.add_circuit(not_gate)

    def add_and(self):
        and_gate = Circuit("AND")
        and_gate.add_component("NAND", self.library.get_circuit(0))
        and_gate.add_component("NOT", self.library.get_circuit("NOT"))
        and_gate.connect_input("A", "NAND", "A")
        and_gate.connect_input("B", "NAND", "B")
        and_gate.connect_output("OUT", "NOT", "OUT")
        and_gate.connect("NAND", "OUT", "NOT", "IN")
        self.library.add_circuit(and_gate)

    def add_or(self):
        or_gate = Circuit("OR")
        or_gate.add_component("NAND_A", self.library.get_circuit(0))
        or_gate.add_component("NAND_B", self.library.get_circuit(0))
        or_gate.add_component("NAND_OUT", self.library.get_circuit(0))

        or_gate.connect_input("A", "NAND_A", "A")
        or_gate.connect_input("A", "NAND_A", "B")
        or_gate.connect_input("B", "NAND_B", "A")
        or_gate.connect_input("B", "NAND_B", "B")

        or_gate.connect_output("OUT", "NAND_OUT", "OUT")

        or_gate.connect("NAND_A", "OUT", "NAND_OUT", "A")
        or_gate.connect("NAND_B", "OUT", "NAND_OUT", "B")

        self.library.add_circuit(or_gate)

    def add_nor(self):
        nor_gate = Circuit("NOR")
        nor_gate.add_component("OR", self.library.get_circuit("OR"))
        nor_gate.add_component("NOT", self.library.get_circuit("NOT"))

        nor_gate.connect_input("A", "OR", "A")
        nor_gate.connect_input("B", "OR", "B")

        nor_gate.connect_output("OUT", "NOT", "OUT")

        nor_gate.connect("OR", "OUT", "NOT", "IN")

        self.library.add_circuit(nor_gate)

    def add_xor(self):
        xor_gate = Circuit("XOR")
        xor_gate.add_component("NAND_A", self.library.get_circuit(0))
        xor_gate.add_component("NAND_B1", self.library.get_circuit(0))
        xor_gate.add_component("NAND_B2", self.library.get_circuit(0))
        xor_gate.add_component("NAND_OUT", self.library.get_circuit(0))

        xor_gate.connect_input("A", "NAND_A", "A")
        xor_gate.connect_input("B", "NAND_A", "B")

        xor_gate.connect_input("A", "NAND_B1", "A")
        xor_gate.connect_input("B", "NAND_B2", "B")

        xor_gate.connect_output("OUT", "NAND_OUT", "OUT")

        xor_gate.connect("NAND_A", "OUT", "NAND_B1", "B")
        xor_gate.connect("NAND_A", "OUT", "NAND_B2", "A")
        xor_gate.connect("NAND_B1", "OUT", "NAND_OUT", "A")
        xor_gate.connect("NAND_B2", "OUT", "NAND_OUT", "B")

        self.library.add_circuit(xor_gate)

    def add_half_adder(self):
        half_adder = Circuit("Half-Adder")
        half_adder.add_component("XOR", self.library.get_circuit("XOR"))
        half_adder.add_component("AND", self.library.get_circuit("AND"))

        half_adder.connect_input("A", "XOR", "A")
        half_adder.connect_input("B", "XOR", "B")
        half_adder.connect_input("A", "AND", "A")
        half_adder.connect_input("B", "AND", "B")

        half_adder.connect_output("SUM", "XOR", "OUT")
        half_adder.connect_output("CARRY", "AND", "OUT")

        self.library.add_circuit(half_adder)

    def add_full_adder(self):
        full_adder = Circuit("Full-Adder")
        full_adder.add_component("XOR_ONE", self.library.get_circuit("XOR"))
        full_adder.add_component("XOR_TWO", self.library.get_circuit("XOR"))
        full_adder.add_component("AND_ONE", self.library.get_circuit("AND"))
        full_adder.add_component("AND_TWO", self.library.get_circuit("AND"))
        full_adder.add_component("OR", self.library.get_circuit("OR"))

        full_adder.connect_input("A", "XOR_ONE", "A")
        full_adder.connect_input("B", "XOR_ONE", "B")

        full_adder.connect_input("A", "AND_ONE", "A")
        full_adder.connect_input("B", "AND_ONE", "B")

        full_adder.connect_input("Cin", "XOR_TWO", "B")
        full_adder.connect_input("Cin", "AND_TWO", "B")

        full_adder.connect_output("SUM", "XOR_TWO", "OUT")
        full_adder.connect_output("Cout", "OR", "OUT")

        full_adder.connect("XOR_ONE", "OUT", "XOR_TWO", "A")
        full_adder.connect("XOR_ONE", "OUT", "AND_TWO", "A")
        full_adder.connect("AND_ONE", "OUT", "OR", "A")
        full_adder.connect("AND_TWO", "OUT", "OR", "B")

        self.library.add_circuit(full_adder)

    def add_2bits_adder(self):
        two_bits_adder = Circuit("2-Bits Adder")
        two_bits_adder.add_component("ADDER_0", self.library.get_circuit("Full-Adder"))
        two_bits_adder.add_component("ADDER_1", self.library.get_circuit("Full-Adder"))

        two_bits_adder.connect_input("A0", "ADDER_0", "A")
        two_bits_adder.connect_input("B0", "ADDER_0", "B")
        two_bits_adder.connect_input("C0", "ADDER_0", "Cin")

        two_bits_adder.connect_input("A1", "ADDER_1", "A")
        two_bits_adder.connect_input("B1", "ADDER_1", "B")

        two_bits_adder.connect("ADDER_0", "Cout", "ADDER_1", "Cin")

        two_bits_adder.connect_output("S0", "ADDER_0", "SUM")
        two_bits_adder.connect_output("S1", "ADDER_1", "SUM")
        two_bits_adder.connect_output("Cout", "ADDER_1", "Cout")

        self.library.add_circuit(two_bits_adder)

    def add_4bits_adder(self):
        four_bits_adder = Circuit("4-Bits Adder")
        four_bits_adder.add_component(
            "2BITS_ADDER_0", self.library.get_circuit("2-Bits Adder")
        )
        four_bits_adder.add_component(
            "2BITS_ADDER_1", self.library.get_circuit("2-Bits Adder")
        )

        four_bits_adder.connect_input("A0", "2BITS_ADDER_0", "A0")
        four_bits_adder.connect_input("B0", "2BITS_ADDER_0", "B0")
        four_bits_adder.connect_input("C0", "2BITS_ADDER_0", "C0")
        four_bits_adder.connect_input("A1", "2BITS_ADDER_0", "A1")
        four_bits_adder.connect_input("B1", "2BITS_ADDER_0", "B1")

        four_bits_adder.connect_input("A2", "2BITS_ADDER_1", "A0")
        four_bits_adder.connect_input("B2", "2BITS_ADDER_1", "B0")
        four_bits_adder.connect_input("A3", "2BITS_ADDER_1", "A1")
        four_bits_adder.connect_input("B3", "2BITS_ADDER_1", "B1")

        four_bits_adder.connect_output("S0", "2BITS_ADDER_0", "S0")
        four_bits_adder.connect_output("S1", "2BITS_ADDER_0", "S1")
        four_bits_adder.connect_output("S2", "2BITS_ADDER_1", "S0")
        four_bits_adder.connect_output("S3", "2BITS_ADDER_1", "S1")
        four_bits_adder.connect_output("Cout", "2BITS_ADDER_1", "Cout")

        four_bits_adder.connect("2BITS_ADDER_0", "Cout", "2BITS_ADDER_1", "C0")

        self.library.add_circuit(four_bits_adder)

    def add_8bits_adder(self):
        eight_bits_adder = Circuit("8-Bits Adder")

        eight_bits_adder.add_component(
            "4BITS_ADDER_0", self.library.get_circuit("4-Bits Adder")
        )
        eight_bits_adder.add_component(
            "4BITS_ADDER_1", self.library.get_circuit("4-Bits Adder")
        )

        eight_bits_adder.connect_input("A0", "4BITS_ADDER_0", "A0")
        eight_bits_adder.connect_input("B0", "4BITS_ADDER_0", "B0")
        eight_bits_adder.connect_input("C0", "4BITS_ADDER_0", "C0")
        eight_bits_adder.connect_input("A1", "4BITS_ADDER_0", "A1")
        eight_bits_adder.connect_input("B1", "4BITS_ADDER_0", "B1")
        eight_bits_adder.connect_input("A2", "4BITS_ADDER_0", "A2")
        eight_bits_adder.connect_input("B2", "4BITS_ADDER_0", "B2")
        eight_bits_adder.connect_input("A3", "4BITS_ADDER_0", "A3")
        eight_bits_adder.connect_input("B3", "4BITS_ADDER_0", "B3")

        eight_bits_adder.connect_input("A4", "4BITS_ADDER_1", "A0")
        eight_bits_adder.connect_input("B4", "4BITS_ADDER_1", "B0")
        eight_bits_adder.connect_input("A5", "4BITS_ADDER_1", "A1")
        eight_bits_adder.connect_input("B5", "4BITS_ADDER_1", "B1")
        eight_bits_adder.connect_input("A6", "4BITS_ADDER_1", "A2")
        eight_bits_adder.connect_input("B6", "4BITS_ADDER_1", "B2")
        eight_bits_adder.connect_input("A7", "4BITS_ADDER_1", "A3")
        eight_bits_adder.connect_input("B7", "4BITS_ADDER_1", "B3")

        eight_bits_adder.connect("4BITS_ADDER_0", "Cout", "4BITS_ADDER_1", "C0")

        eight_bits_adder.connect_output("S0", "4BITS_ADDER_0", "S0")
        eight_bits_adder.connect_output("S1", "4BITS_ADDER_0", "S1")
        eight_bits_adder.connect_output("S2", "4BITS_ADDER_0", "S2")
        eight_bits_adder.connect_output("S3", "4BITS_ADDER_0", "S3")

        eight_bits_adder.connect_output("S4", "4BITS_ADDER_1", "S0")
        eight_bits_adder.connect_output("S5", "4BITS_ADDER_1", "S1")
        eight_bits_adder.connect_output("S6", "4BITS_ADDER_1", "S2")
        eight_bits_adder.connect_output("S7", "4BITS_ADDER_1", "S3")

        eight_bits_adder.connect_output("Cout", "4BITS_ADDER_1", "Cout")

        self.library.add_circuit(eight_bits_adder)
