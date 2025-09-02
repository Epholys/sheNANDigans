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

        or_gate.add_component("NOT_A", self.library.get_circuit("NOT"))
        or_gate.add_component("NOT_B", self.library.get_circuit("NOT"))
        or_gate.add_component("AND", self.library.get_circuit("AND"))
        or_gate.add_component("NOT_OUT", self.library.get_circuit("NOT"))

        or_gate.connect_input("A", "NOT_A", "IN")
        or_gate.connect_input("B", "NOT_B", "IN")

        or_gate.connect_output("OUT", "NOT_OUT", "OUT")

        or_gate.connect("NOT_A", "OUT", "AND", "A")
        or_gate.connect("NOT_B", "OUT", "AND", "B")
        or_gate.connect("AND", "OUT", "NOT_OUT", "IN")

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

        xor_gate.connect_output("OUT", "OR", "OUT")

        xor_gate.connect("NOT_A", "OUT", "AND_B", "B")
        xor_gate.connect("NOT_B", "OUT", "AND_A", "B")
        xor_gate.connect("AND_A", "OUT", "OR", "A")
        xor_gate.connect("AND_B", "OUT", "OR", "B")

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

        mux.connect_output("OUT", "AND", "OUT")

        mux.connect("SEL_NOT", "OUT", "OR_B", "B")
        mux.connect("OR_A", "OUT", "AND", "A")
        mux.connect("OR_B", "OUT", "AND", "B")

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

        dmux.connect_output("A", "AND_A", "OUT")
        dmux.connect_output("B", "AND_B", "OUT")

        dmux.connect("NOT", "OUT", "AND_A", "B")

        self.library.add_circuit(dmux)
