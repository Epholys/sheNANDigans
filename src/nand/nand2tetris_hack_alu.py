from nand.circuit import Circuit
from nand.circuit_builder import CircuitBuilder


class HackALUBuilder(CircuitBuilder):
    def __init__(self):
        super().__init__()

    def build_circuits(self):
        super().build_circuits()
        self.add_not()
        self.add_and()
        self.add_or()
        self.add_xor()
        self.add_mux()
        self.add_dmux()
        self.add_not16()
        self.add_and16()
        self.add_or16()
        self.add_mux16()
        self.add_or8way()
        self.add_mux4way16()
        self.add_mux8way16()

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
        and_gate.connect("NAND", "OUT", "NOT", "IN")
        and_gate.connect_output("OUT", "NOT", "OUT")
        self.library.add_circuit(and_gate)

    def add_or(self):
        or_gate = Circuit("OR")

        or_gate.add_component("NOT_A", self.library.get_circuit("NOT"))
        or_gate.add_component("NOT_B", self.library.get_circuit("NOT"))
        or_gate.add_component("AND", self.library.get_circuit("AND"))
        or_gate.add_component("NOT_OUT", self.library.get_circuit("NOT"))

        or_gate.connect_input("A", "NOT_A", "IN")
        or_gate.connect_input("B", "NOT_B", "IN")

        or_gate.connect("NOT_A", "OUT", "AND", "A")
        or_gate.connect("NOT_B", "OUT", "AND", "B")
        or_gate.connect("AND", "OUT", "NOT_OUT", "IN")

        or_gate.connect_output("OUT", "NOT_OUT", "OUT")

        self.library.add_circuit(or_gate)

    def add_xor(self):
        xor_gate = Circuit("XOR")

        xor_gate.add_component("NOT_A", self.library.get_circuit("NOT"))
        xor_gate.add_component("NOT_B", self.library.get_circuit("NOT"))
        xor_gate.add_component("AND_A", self.library.get_circuit("AND"))
        xor_gate.add_component("AND_B", self.library.get_circuit("AND"))
        xor_gate.add_component("OR", self.library.get_circuit("OR"))

        xor_gate.connect_input("A", "NOT_A", "IN")
        xor_gate.connect_input("B", "NOT_B", "IN")
        xor_gate.connect_input("A", "AND_A", "A")
        xor_gate.connect_input("B", "AND_B", "A")

        xor_gate.connect("NOT_A", "OUT", "AND_B", "B")
        xor_gate.connect("NOT_B", "OUT", "AND_A", "B")
        xor_gate.connect("AND_A", "OUT", "OR", "A")
        xor_gate.connect("AND_B", "OUT", "OR", "B")

        xor_gate.connect_output("OUT", "OR", "OUT")

        self.library.add_circuit(xor_gate)

    def add_mux(self):
        mux = Circuit("Mux")

        mux.add_component("SEL_NOT", self.library.get_circuit("NOT"))
        mux.add_component("OR_A", self.library.get_circuit("OR"))
        mux.add_component("OR_B", self.library.get_circuit("OR"))
        mux.add_component("AND", self.library.get_circuit("AND"))

        mux.connect_input("SEL", "SEL_NOT", "IN")
        mux.connect_input("A", "OR_A", "A")
        mux.connect_input("SEL", "OR_A", "B")
        mux.connect_input("B", "OR_B", "A")

        mux.connect("SEL_NOT", "OUT", "OR_B", "B")
        mux.connect("OR_A", "OUT", "AND", "A")
        mux.connect("OR_B", "OUT", "AND", "B")

        mux.connect_output("OUT", "AND", "OUT")

        self.library.add_circuit(mux)

    def add_dmux(self):
        dmux = Circuit("DMux")

        dmux.add_component("NOT", self.library.get_circuit("NOT"))
        dmux.add_component("AND_A", self.library.get_circuit("AND"))
        dmux.add_component("AND_B", self.library.get_circuit("AND"))

        dmux.connect_input("IN", "AND_A", "A")
        dmux.connect_input("SEL", "NOT", "IN")
        dmux.connect_input("IN", "AND_B", "A")
        dmux.connect_input("SEL", "AND_B", "B")

        dmux.connect("NOT", "OUT", "AND_A", "B")

        dmux.connect_output("A", "AND_A", "OUT")
        dmux.connect_output("B", "AND_B", "OUT")

        self.library.add_circuit(dmux)

    def add_not16(self):
        not16 = Circuit("NOT16")

        for i in range(16):
            not16.add_component(f"NOT_{i}", self.library.get_circuit("NOT"))
            not16.connect_input(f"IN_{i}", f"NOT_{i}", "IN")
            not16.connect_output(f"OUT_{i}", f"NOT_{i}", "OUT")

        self.library.add_circuit(not16)

    def add_and16(self):
        and16 = Circuit("AND16")

        for i in range(16):
            and16.add_component(f"AND_{i}", self.library.get_circuit("AND"))

            and16.connect_input(f"A_{i}", f"AND_{i}", "A")
            and16.connect_input(f"B_{i}", f"AND_{i}", "B")

            and16.connect_output(f"OUT_{i}", f"AND_{i}", "OUT")

        self.library.add_circuit(and16)

    def add_or16(self):
        or16 = Circuit("OR16")

        for i in range(16):
            or16.add_component(f"OR_{i}", self.library.get_circuit("OR"))

            or16.connect_input(f"A_{i}", f"OR_{i}", "A")
            or16.connect_input(f"B_{i}", f"OR_{i}", "B")

            or16.connect_output(f"OUT_{i}", f"OR_{i}", "OUT")

        self.library.add_circuit(or16)

    def add_mux16(self):
        mux16 = Circuit("Mux16")

        for i in range(16):
            mux16.add_component(f"Mux_{i}", self.library.get_circuit("Mux"))

            mux16.connect_input(f"A_{i}", f"Mux_{i}", "A")
            mux16.connect_input(f"B_{i}", f"Mux_{i}", "B")
            mux16.connect_input("SEL", f"Mux_{i}", "SEL")

            mux16.connect_output(f"OUT_{i}", f"Mux_{i}", "OUT")

        self.library.add_circuit(mux16)

    def add_or8way(self):
        or8way = Circuit("OR8Way")

        # 7 ORs: 4 for the first level, 2 for the second, 1 for the last.
        for i in range(7):
            or8way.add_component(f"OR_{i}", self.library.get_circuit("OR"))

        # Inputs go pairwise in the first ORs level.
        for i in range(8):
            or_level_1 = i // 2
            or_input = "A" if i % 2 == 0 else "B"
            or8way.connect_input(f"IN_{i}", f"OR_{or_level_1}", or_input)

        # Connections between layers: output of the layer before go into the inputs of
        # the layer after.
        for i in range(6):
            # +4: the first 4 are the first layer.
            or_level_2 = (i // 2) + 4
            or_input = "A" if i % 2 == 0 else "B"
            or8way.connect(f"OR_{i}", "OUT", f"OR_{or_level_2}", or_input)

        or8way.connect_output("OUT", "OR_6", "OUT")

        self.library.add_circuit(or8way)

    def add_mux4way16(self):
        mux4way16 = Circuit("Mux4Way16")

        mux4way16.add_component("Mux16_AB", self.library.get_circuit("Mux16"))
        mux4way16.add_component("Mux16_CD", self.library.get_circuit("Mux16"))
        mux4way16.add_component("Mux16_OUT", self.library.get_circuit("Mux16"))

        for i in range(16):
            mux4way16.connect_input(f"A_{i}", "Mux16_AB", f"A_{i}")
            mux4way16.connect_input(f"B_{i}", "Mux16_AB", f"B_{i}")
            mux4way16.connect_input(f"C_{i}", "Mux16_CD", f"A_{i}")
            mux4way16.connect_input(f"D_{i}", "Mux16_CD", f"B_{i}")

        mux4way16.connect_input("SEL_0", "Mux16_AB", "SEL")
        mux4way16.connect_input("SEL_0", "Mux16_CD", "SEL")
        mux4way16.connect_input("SEL_1", "Mux16_OUT", "SEL")

        for i in range(16):
            mux4way16.connect("Mux16_AB", f"OUT_{i}", "Mux16_OUT", f"A_{i}")
            mux4way16.connect("Mux16_CD", f"OUT_{i}", "Mux16_OUT", f"B_{i}")

        for i in range(16):
            mux4way16.connect_output(f"OUT_{i}", "Mux16_OUT", f"OUT_{i}")

        self.library.add_circuit(mux4way16)

    def add_mux8way16(self):
        mux8way16 = Circuit("Mux8Way16")

        mux8way16.add_component("Mux4Way16_ABCD", self.library.get_circuit("Mux4Way16"))
        mux8way16.add_component("Mux4Way16_EFGH", self.library.get_circuit("Mux4Way16"))
        mux8way16.add_component("Mux16_OUT", self.library.get_circuit("Mux16"))

        for i in range(16):
            mux8way16.connect_input(f"A_{i}", "Mux4Way16_ABCD", f"A_{i}")
            mux8way16.connect_input(f"B_{i}", "Mux4Way16_ABCD", f"B_{i}")
            mux8way16.connect_input(f"C_{i}", "Mux4Way16_ABCD", f"C_{i}")
            mux8way16.connect_input(f"D_{i}", "Mux4Way16_ABCD", f"D_{i}")
            mux8way16.connect_input(f"E_{i}", "Mux4Way16_EFGH", f"A_{i}")
            mux8way16.connect_input(f"F_{i}", "Mux4Way16_EFGH", f"B_{i}")
            mux8way16.connect_input(f"G_{i}", "Mux4Way16_EFGH", f"C_{i}")
            mux8way16.connect_input(f"H_{i}", "Mux4Way16_EFGH", f"D_{i}")

        mux8way16.connect_input("SEL_0", "Mux4Way16_ABCD", "SEL_0")
        mux8way16.connect_input("SEL_1", "Mux4Way16_ABCD", "SEL_1")
        mux8way16.connect_input("SEL_0", "Mux4Way16_EFGH", "SEL_0")
        mux8way16.connect_input("SEL_1", "Mux4Way16_EFGH", "SEL_1")
        mux8way16.connect_input("SEL_2", "Mux16_OUT", "SEL")

        for i in range(16):
            mux8way16.connect("Mux4Way16_ABCD", f"OUT_{i}", "Mux16_OUT", f"A_{i}")
            mux8way16.connect("Mux4Way16_EFGH", f"OUT_{i}", "Mux16_OUT", f"B_{i}")

        for i in range(16):
            mux8way16.connect_output(f"OUT_{i}", "Mux16_OUT", f"OUT_{i}")

        self.library.add_circuit(mux8way16)
