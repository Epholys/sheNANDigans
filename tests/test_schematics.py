from src import *

from itertools import product
from typing import Callable, List, OrderedDict
import unittest
from parameterized import parameterized_class

from src import schematics
from src.circuit import Circuit, CircuitId
from src.decoding import CircuitDecoder
from src.encoding import CircuitEncoder


builder = schematics.SchematicsBuilder()
builder.build_circuits()
reference = builder.schematics

encoder = CircuitEncoder(reference.copy())
encoded : List[int] = encoder.encode()
decoder = CircuitDecoder(encoded.copy())
round_trip : OrderedDict[CircuitId, Circuit]  = decoder.decode()    

@parameterized_class([{'library': reference}, {'library': round_trip}])
class TestSchematics(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()