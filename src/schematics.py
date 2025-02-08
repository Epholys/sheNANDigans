from copy import deepcopy
from typing import OrderedDict

from circuit import Circuit, Wire

schematics = OrderedDict()

def add_schematic(circuit):
    if schematics.get(circuit.identifier) is not None:
        raise ValueError(f"Circuit {circuit.identifier} already exists")
    schematics[circuit.identifier] = circuit

def get_schematic(identifier):
    if schematics.get(identifier) is None:
        raise ValueError(f"Circuit {identifier} does not exist")
    return deepcopy(schematics[identifier])

def add_circuits():
    add_nand()
    add_not()
    add_and()
    add_or()
    add_nor()
    add_xor()
    add_half_adder()
    
def add_nand():
    nand_gate = Circuit(identifier="NAND")
    nand_gate.inputs["A"] = Wire()
    nand_gate.inputs["B"] = Wire()
    nand_gate.outputs["OUT"] = Wire()
    add_schematic(nand_gate)


def add_not():
    not_gate = Circuit(identifier="NOT")
    not_gate.add_component("NAND", get_schematic("NAND"))
    not_gate.add_input("IN", "NAND", "A")
    not_gate.add_input("IN", "NAND", "B")
    not_gate.add_output("OUT", "NAND", "OUT")
    add_schematic(not_gate)

def add_and():
    and_gate = Circuit(identifier="AND")
    and_gate.add_component("NAND", get_schematic("NAND"))
    and_gate.add_component("NOT", get_schematic("NOT"))
    and_gate.add_input("A", "NAND", "A")
    and_gate.add_input("B", "NAND", "B")
    and_gate.add_output("OUT", "NOT", "OUT")
    and_gate.add_wire("NAND", "OUT", "NOT", "IN")
    add_schematic(and_gate)

def add_or():
    or_gate = Circuit(identifier="OR")
    or_gate.add_component("NAND_A", get_schematic("NAND"))
    or_gate.add_component("NAND_B", get_schematic("NAND"))
    or_gate.add_component("NAND_OUT", get_schematic("NAND"))

    or_gate.add_input("A", "NAND_A", "A")
    or_gate.add_input("A", "NAND_A", "B")
    or_gate.add_input("B", "NAND_B", "A")
    or_gate.add_input("B", "NAND_B", "B")

    or_gate.add_output("OUT", "NAND_OUT", "OUT")

    or_gate.add_wire("NAND_A", "OUT", "NAND_OUT", "A")
    or_gate.add_wire("NAND_B", "OUT", "NAND_OUT", "B")

    add_schematic(or_gate)

def add_nor():
    nor_gate = Circuit(identifier="NOR")
    nor_gate.add_component("OR", get_schematic("OR"))
    nor_gate.add_component("NOT", get_schematic("NOT"))

    nor_gate.add_input("A", "OR", "A")    
    nor_gate.add_input("B", "OR", "B")

    nor_gate.add_output("OUT", "NOT", "OUT")

    nor_gate.add_wire("OR", "OUT", "NOT", "IN")

    add_schematic(nor_gate)

def add_xor():
    xor_gate = Circuit(identifier="XOR")
    xor_gate.add_component("NAND_A", get_schematic("NAND"))
    xor_gate.add_component("NAND_B1", get_schematic("NAND"))
    xor_gate.add_component("NAND_B2", get_schematic("NAND"))
    xor_gate.add_component("NAND_OUT", get_schematic("NAND"))

    xor_gate.add_input("A", "NAND_A", "A")
    xor_gate.add_input("B", "NAND_A", "B")
    
    xor_gate.add_input("A", "NAND_B1", "A")
    xor_gate.add_input("B", "NAND_B2", "B")

    xor_gate.add_output("OUT", "NAND_OUT", "OUT")

    xor_gate.add_wire("NAND_A", "OUT", "NAND_B1", "B")
    xor_gate.add_wire("NAND_A", "OUT", "NAND_B2", "A")
    xor_gate.add_wire("NAND_B1", "OUT", "NAND_OUT", "A")
    xor_gate.add_wire("NAND_B2", "OUT", "NAND_OUT", "B")

    add_schematic(xor_gate)

def add_half_adder():
    half_adder = Circuit(identifier="HALF_ADDER")
    half_adder.add_component("XOR", get_schematic("XOR"))
    half_adder.add_component("AND", get_schematic("AND"))

    half_adder.add_input("A", "XOR", "A")
    half_adder.add_input("B", "XOR", "B")
    half_adder.add_input("A", "AND", "A")
    half_adder.add_input("B", "AND", "B")

    half_adder.add_output("SUM", "XOR", "OUT")
    half_adder.add_output("CARRY", "AND", "OUT")

    add_schematic(half_adder)