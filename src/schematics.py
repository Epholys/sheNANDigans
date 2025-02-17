from copy import deepcopy
from typing import OrderedDict

from circuit import Circuit, CircuitDict, CircuitKey, Wire

def add_nand(library: CircuitDict):
    nand_gate = Circuit(0)
    nand_gate.inputs["A"] = Wire()
    nand_gate.inputs["B"] = Wire()
    nand_gate.outputs["OUT"] = Wire()
    add_schematic(nand_gate, library)

def add_schematic(circuit: Circuit, library: CircuitDict):
    if library.get(circuit.identifier) is not None:
        raise ValueError(f"Circuit {circuit.identifier} already exists")
    library[circuit.identifier] = circuit

def get_schematic(identifier : CircuitKey, library : CircuitDict) -> Circuit:
    if library.get(identifier) is None:
        raise ValueError(f"Circuit {identifier} does not exist")
    return deepcopy(library[identifier])

class SchematicsBuilder:
    def __init__(self):
        self.schematics : CircuitDict = OrderedDict()

    def add_schematic(self, circuit: Circuit):
        add_schematic(circuit, self.schematics)
    
    def get_schematic(self, id : CircuitKey):
        return get_schematic(id, self.schematics)

    def build_circuits(self):
        add_nand(self.schematics)
        self.add_not()
        self.add_and()
        self.add_or()
        self.add_nor()
        self.add_xor()
        self.add_half_adder()

    def add_not(self):
        not_gate = Circuit(1)
        not_gate.add_component("NAND", self.get_schematic(0))
        not_gate.connect_input("IN", "NAND", "A")
        not_gate.connect_input("IN", "NAND", "B")
        not_gate.connect_output("OUT", "NAND", "OUT")
        self.add_schematic(not_gate)

    def add_and(self):
        and_gate = Circuit(2)
        and_gate.add_component("NAND", self.get_schematic(0))
        and_gate.add_component("NOT", self.get_schematic(1))
        and_gate.connect_input("A", "NAND", "A")
        and_gate.connect_input("B", "NAND", "B")
        and_gate.connect_output("OUT", "NOT", "OUT")
        and_gate.connect("NAND", "OUT", "NOT", "IN")
        self.add_schematic(and_gate)

    def add_or(self):
        or_gate = Circuit(3)
        or_gate.add_component("NAND_A", self.get_schematic(0))
        or_gate.add_component("NAND_B", self.get_schematic(0))
        or_gate.add_component("NAND_OUT", self.get_schematic(0))

        or_gate.connect_input("A", "NAND_A", "A")
        or_gate.connect_input("A", "NAND_A", "B")
        or_gate.connect_input("B", "NAND_B", "A")
        or_gate.connect_input("B", "NAND_B", "B")

        or_gate.connect_output("OUT", "NAND_OUT", "OUT")

        or_gate.connect("NAND_A", "OUT", "NAND_OUT", "A")
        or_gate.connect("NAND_B", "OUT", "NAND_OUT", "B")

        self.add_schematic(or_gate)

    def add_nor(self):
        nor_gate = Circuit(4)
        nor_gate.add_component("OR", self.get_schematic(3))
        nor_gate.add_component("NOT", self.get_schematic(1))

        nor_gate.connect_input("A", "OR", "A")    
        nor_gate.connect_input("B", "OR", "B")

        nor_gate.connect_output("OUT", "NOT", "OUT")

        nor_gate.connect("OR", "OUT", "NOT", "IN")

        self.add_schematic(nor_gate)

    def add_xor(self):
        xor_gate = Circuit(5)
        xor_gate.add_component("NAND_A", self.get_schematic(0))
        xor_gate.add_component("NAND_B1", self.get_schematic(0))
        xor_gate.add_component("NAND_B2", self.get_schematic(0))
        xor_gate.add_component("NAND_OUT", self.get_schematic(0))

        xor_gate.connect_input("A", "NAND_A", "A")
        xor_gate.connect_input("B", "NAND_A", "B")

        xor_gate.connect_input("A", "NAND_B1", "A")
        xor_gate.connect_input("B", "NAND_B2", "B")

        xor_gate.connect_output("OUT", "NAND_OUT", "OUT")

        xor_gate.connect("NAND_A", "OUT", "NAND_B1", "B")
        xor_gate.connect("NAND_A", "OUT", "NAND_B2", "A")
        xor_gate.connect("NAND_B1", "OUT", "NAND_OUT", "A")
        xor_gate.connect("NAND_B2", "OUT", "NAND_OUT", "B")

        self.add_schematic(xor_gate)

    def add_half_adder(self):
        half_adder = Circuit(6)
        half_adder.add_component("XOR", self.get_schematic(5))
        half_adder.add_component("AND", self.get_schematic(2))

        half_adder.connect_input("A", "XOR", "A")
        half_adder.connect_input("B", "XOR", "B")
        half_adder.connect_input("A", "AND", "A")
        half_adder.connect_input("B", "AND", "B")

        half_adder.connect_output("SUM", "XOR", "OUT")
        half_adder.connect_output("CARRY", "AND", "OUT")

        self.add_schematic(half_adder)