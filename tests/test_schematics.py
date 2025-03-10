from itertools import product
from typing import Callable, List, OrderedDict
import unittest
from parameterized import parameterized_class  # type: ignore

from src import schematics
from src.circuit import Circuit, CircuitKey
from src.decoding import CircuitDecoder
from src.encoding import CircuitEncoder


builder = schematics.SchematicsBuilder()
builder.build_circuits()
reference_circuits = builder.schematics

encoded = CircuitEncoder(reference_circuits).encode()
round_trip_circuits = CircuitDecoder(encoded).decode()


@parameterized_class(
    [{"library": reference_circuits}, {"library": round_trip_circuits}]
)
class TestSchematics(unittest.TestCase):
    library: OrderedDict[CircuitKey, Circuit]

    def assert_2_in_1_out(
        self, gate: Circuit, gate_logic: Callable[[bool, bool], bool]
    ):
        self.assertEqual(len(gate.inputs), 2)
        inputs = list(gate.inputs.values())
        input_a = inputs[0]
        input_b = inputs[1]

        self.assertEqual(len(gate.outputs), 1)
        output = list(gate.outputs.values())[0]

        possible_inputs = list(product([True, False], repeat=2))
        expected_outputs = [gate_logic(a, b) for a, b in possible_inputs]

        for (a, b), expected_output in zip(possible_inputs, expected_outputs):
            gate.reset()
            input_a.state = a
            input_b.state = b
            self.assertTrue(gate.simulate(), "Simulation failed")
            self.assertEqual(bool(output.state), expected_output)

    def test_nand(self):
        nand_gate = schematics.get_schematic_idx(0, self.library)
        self.assert_2_in_1_out(nand_gate, lambda a, b: not (a and b))

    def test_not(self):
        not_gate = schematics.get_schematic_idx(1, self.library)

        self.assertEqual(len(not_gate.inputs), 1)
        input = list(not_gate.inputs.values())[0]

        self.assertEqual(len(not_gate.outputs), 1)
        output = list(not_gate.outputs.values())[0]

        for a in [True, False]:
            not_gate.reset()
            input.state = a
            self.assertTrue(not_gate.simulate())
            self.assertEqual(bool(output.state), not a)

    def test_and(self):
        and_gate = schematics.get_schematic_idx(2, self.library)
        self.assert_2_in_1_out(and_gate, lambda a, b: a and b)

    def test_or(self):
        or_gate = schematics.get_schematic_idx(3, self.library)
        self.assert_2_in_1_out(or_gate, lambda a, b: a or b)

    def test_nor(self):
        nor_gate = schematics.get_schematic_idx(4, self.library)
        self.assert_2_in_1_out(nor_gate, lambda a, b: not (a or b))

    def test_xor(self):
        xor_gate = schematics.get_schematic_idx(5, self.library)
        self.assert_2_in_1_out(xor_gate, lambda a, b: a ^ b)

    def assert_numeric_operations(
        self,
        circuit: Circuit,
        n_inputs: int,
        n_outputs: int,
        inputs_to_numbers: Callable[[List[bool]], List[int]],
        number_to_outputs: Callable[[int], List[bool]],
        operation: Callable[[List[int]], int],
    ):
        self.assertEqual(len(circuit.inputs), n_inputs)
        input_wires = list(circuit.inputs.values())

        self.assertEqual(len(circuit.outputs), n_outputs)
        output_wires = list(circuit.outputs.values())

        all_possible_inputs = list(product([True, False], repeat=n_inputs))

        all_expected_outputs: List[List[bool]] = []
        for possible_input in all_possible_inputs:
            input_numbers = inputs_to_numbers(list(possible_input))
            operation_result = operation(input_numbers)
            all_expected_outputs.append(number_to_outputs(operation_result))

        for possible_input, expected_outputs in zip(
            all_possible_inputs, all_expected_outputs
        ):
            circuit.reset()

            for input_wire, input in zip(input_wires, possible_input):
                input_wire.state = input

            self.assertTrue(circuit.simulate(), "Simulation failed")

            actual_outputs = [bool(wire.state) for wire in output_wires]

            self.assertEqual(actual_outputs, expected_outputs)

    def test_half_adder(self):
        half_adder = schematics.get_schematic_idx(6, self.library)

        # Inputs : a, b
        # Operation : a + b
        # Output : sum, carry
        # Ex: a=1, b=0 / 1 + 0 = 2 = 0b01 / sum:1, carry:0

        def inputs_to_numbers(inputs: List[bool]):
            self.assertEqual(len(inputs), 2)
            return [+(b) for b in inputs]

        def number_to_output(number: int):
            sum = number & 1
            carry = (number >> 1) & 1
            return [bool(x) for x in [sum, carry]]

        self.assert_numeric_operations(
            half_adder, 2, 2, inputs_to_numbers, number_to_output, sum
        )

    def test_full_adder(self):
        full_adder = schematics.get_schematic_idx(7, self.library)
        # Inputs : a, b, cin
        # Operation : a + b + cin
        # Output : sum, cout
        # Ex: a=1, b=0, cin=1 / 1 + 0 + 1 = 2 = 0b10 / sum:0, cout:1

        def inputs_to_numbers(inputs: List[bool]):
            self.assertEqual(len(inputs), 3)
            return [+(b) for b in inputs]

        def number_to_output(number: int):
            sum = number & 1
            carry = (number >> 1) & 1
            return [bool(x) for x in [sum, carry]]

        self.assert_numeric_operations(
            full_adder, 3, 2, inputs_to_numbers, number_to_output, sum
        )

    def test_2bits_adder(self):
        two_bits_adder = schematics.get_schematic_idx(8, self.library)
        # Inputs : a0, b0, c0, a1, b1
        # Outputs: s0, s1, cout
        # Input Numbers  : A = 0b_a1_a0 ; B = 0b_b1_b0 ; Carry = c0
        # Output Numbers : S = 0b_cout_s1_s0
        # Operation : A + B + Carry = S
        # Ex: a0=1, a1=0, cin=1, b1=1, b0=0
        # A = 0b01 = 1
        # B = 0b10 = 2
        # Carry = 0b1 = 1
        # Operation : 1 + 2 + 1 = 4 = 0b100
        # Outputs = s0=0 ; s1=1 ; cout=1

        def inputs_to_numbers(inputs: List[bool]):
            self.assertEqual(len(inputs), 5)
            a0 = +(inputs[0])
            b0 = +(inputs[1])
            c0 = +(inputs[2])
            a1 = +(inputs[3])
            b1 = +(inputs[4])

            a = a1 * 2 + a0
            b = b1 * 2 + b0

            return [a, b, c0]

        def number_to_output(number: int):
            cout = (number >> 2) & 1
            s1 = (number >> 1) & 1
            s0 = number & 1

            return [bool(x) for x in [s0, s1, cout]]

        self.assert_numeric_operations(
            two_bits_adder, 5, 3, inputs_to_numbers, number_to_output, sum
        )


if __name__ == "__main__":
    unittest.main()
