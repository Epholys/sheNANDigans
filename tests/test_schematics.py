from src import *

from itertools import product
from typing import Callable, OrderedDict
import unittest
from parameterized import parameterized_class # type: ignore

from src import schematics
from src.circuit import Circuit, CircuitKey
from src.decoding import CircuitDecoder
from src.encoding import CircuitEncoder


builder = schematics.SchematicsBuilder()
builder.build_circuits()
reference = builder.schematics

encoder = CircuitEncoder(reference.copy())
encoded = encoder.encode()
decoder = CircuitDecoder(encoded.copy())
round_trip = decoder.decode()    

@parameterized_class([{'library': reference}, {'library': round_trip}])
class TestSchematics(unittest.TestCase):

    library: OrderedDict[CircuitKey, Circuit]

    def assert_2_in_1_out(self, gate : Circuit, gate_logic : Callable[[bool, bool], bool]):
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
        nand_gate = schematics.get_schematic(0, self.library)        
        self.assert_2_in_1_out(nand_gate, lambda a, b: not (a and b))

    def test_not(self):
        not_gate = schematics.get_schematic(1, self.library)       
        
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
        and_gate = schematics.get_schematic(2, self.library)        
        self.assert_2_in_1_out(and_gate, lambda a, b: a and b)

    def test_or(self):
        or_gate = schematics.get_schematic(3, self.library)
        self.assert_2_in_1_out(or_gate, lambda a, b: a or b)

    def test_nor(self):
        nor_gate = schematics.get_schematic(4, self.library)
        self.assert_2_in_1_out(nor_gate, lambda a, b: not(a or b))

    def test_xor(self):
        xor_gate = schematics.get_schematic(5, self.library)
        self.assert_2_in_1_out(xor_gate, lambda a, b: a ^ b)

    def test_half_adder(self):
        half_adder = schematics.get_schematic(6, self.library)
        self.assertEqual(len(half_adder.inputs), 2)
        inputs = list(half_adder.inputs.values())
        input_a = inputs[0]
        input_b = inputs[1]
        
        self.assertEqual(len(half_adder.outputs), 2)
        outputs = list(half_adder.outputs.values())
        sum_output = outputs[0]
        carry_output = outputs[1]

        possible_inputs = list(product([True, False], repeat=2))
        # +(True) = 1, +(False) = 0
        addition = [+(a) + (+b) for (a, b) in possible_inputs]
        # Pour : a=True, b=False -> sum=0b01 -> bit=sum&1=1, carry=(sum>>1)&1=0
        expected_outputs = [(sum & 1, (sum >> 1) & 1) for sum in addition]

        for (a, b), (sum, carry) in zip(possible_inputs, expected_outputs):
            half_adder.reset()
            input_a.state = a
            input_b.state = b
            self.assertTrue(half_adder.simulate(), "Simulation failed")

            sum_result = int(sum_output.state)
            carry_result = int(carry_output.state)
            self.assertEqual((sum_result, carry_result), (sum, carry))

    def test_full_adder(self):
        full_adder = schematics.get_schematic(7, self.library)
        self.assertEqual(len(full_adder.inputs), 3)
        inputs = list(full_adder.inputs.values())
        input_a = inputs[0]
        input_b = inputs[1]
        input_cin = inputs[2]
        
        self.assertEqual(len(full_adder.outputs), 2)
        outputs = list(full_adder.outputs.values())
        sum_output = outputs[0]
        cout_output = outputs[1]

        possible_inputs = list(product([True, False], repeat=3))
        # +(True) = 1, +(False) = 0
        addition = [+(a) + (+b) + (+cin) for (a, b, cin) in possible_inputs]
        # Pour : a=True, b=False -> sum=0b01 -> bit=sum&1=1, carry=(sum>>1)&1=0
        expected_outputs = [(sum & 1, (sum >> 1) & 1) for sum in addition]

        for (a, b, cin), (sum, cout) in zip(possible_inputs, expected_outputs):
            full_adder.reset()
            input_a.state = a
            input_b.state = b
            input_cin.state = cin
            self.assertTrue(full_adder.simulate(), "Simulation failed")

            sum_result = int(sum_output.state)
            carry_result = int(cout_output.state)
            self.assertEqual((sum_result, carry_result), (sum, cout))  

    def test_2bits_adder(self):
        two_bits_adder = schematics.get_schematic(8, self.library)
        self.assertEqual(len(two_bits_adder.inputs), 5)
        inputs = list(two_bits_adder.inputs.values())
        input_a0 = inputs[0]
        input_b0 = inputs[1]
        input_c0 = inputs[2]
        input_a1 = inputs[3]
        input_b1 = inputs[4]

        self.assertEqual(len(two_bits_adder.outputs), 3)
        outputs = list(two_bits_adder.outputs.values())
        s0_output = outputs[0]
        s1_output = outputs[1]
        cout_output = outputs[2]

        possible_inputs = list(product([True, False], repeat=5))
        # +(True) = 1, +(False) = 0
        addition = [+(a0) + +(b0) + +(a1) * 2 + +(b1) * 2 + +(c0) for (a0, b0, a1, b1, c0) in possible_inputs]
        # Pour : a=True, b=False -> sum=0b01 -> bit=sum&1=1, carry=(sum>>1)&1=0
        expected_outputs = [(sum & 1, (sum >> 1) & 1, (sum >> 2) & 1) for sum in addition]

        for (inputs, addition_total, outputs) in zip(possible_inputs, addition, expected_outputs):
            if addition_total == 6:
                print(f"inputs = {[+(x) for x in inputs]}")
                print(f"addition = {addition_total}")
                print(f"outputs = {outputs}")
                print(f"addition_outputs = {[]}")
                print("")

        for idx, ((a0, b0, a1, b1, c0), (s0, s1, cout)) in enumerate(zip(possible_inputs, expected_outputs)):
            two_bits_adder.reset()
            input_a0.state = a0
            input_b0.state = b0
            input_a1.state = a1
            input_b1.state = b1
            input_c0.state = c0
            
            self.assertTrue(two_bits_adder.simulate(), "Simulation failed")

            s0_result = int(s0_output.state)
            s1_result = int(s1_output.state)
            carry_result = int(cout_output.state)

            
            if addition[idx] == 6:
                print(f"possible_inputs[{idx}] = {[+(x) for x in possible_inputs[idx]]}")
                print(f"addition[{idx}] = {addition[idx]}")
                print(f"expected_outputs[{idx}] = {expected_outputs[idx]}")
                print(f"result = {s0_result + s1_result * 2 + carry_result * 4}")
                print((s0_result, s1_result, carry_result), (s0, s1, cout))


            self.assertEqual((s0_result, s1_result, carry_result), (s0, s1, cout))    
            print("")

if __name__ == '__main__':
    unittest.main()