from itertools import product
import unittest

from src import schematics

class TestSchematics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schematics.add_circuits()
    

    def assert_2_in_1_out(self, gate, gate_logic):
        self.assertEqual(len(gate.inputs), 2)
        inputs = list(gate.inputs.keys())
        input_a = inputs[0]
        input_b = inputs[1]
        
        self.assertEqual(len(gate.outputs), 1)
        output = list(gate.outputs.keys())[0]

        possible_inputs = list(product([True, False], repeat=2))
        expected_outputs = [gate_logic(a, b) for a, b in possible_inputs]

        for (a, b), expected_output in zip(possible_inputs, expected_outputs):
            gate.reset()
            gate.inputs[input_a].state = a
            gate.inputs[input_b].state = b
            self.assertTrue(gate.simulate(), "Simulation failed")
            self.assertEqual(gate.outputs[output].state, expected_output)


    def test_nand(self):
        nand_gate = schematics.get_schematic("NAND")        
        self.assert_2_in_1_out(nand_gate, lambda a, b: not (a and b))

    def test_not(self):
        not_gate = schematics.get_schematic("NOT")        
        
        self.assertEqual(len(not_gate.inputs), 1)
        input = list(not_gate.inputs.keys())[0]
        
        self.assertEqual(len(not_gate.outputs), 1)
        output = list(not_gate.outputs.keys())[0]
        
        for a in [True, False]:
            not_gate.reset()
            not_gate.inputs[input].state = a
            self.assertTrue(not_gate.simulate())
            self.assertEqual(not_gate.outputs[output].state, not a)

    def test_and(self):
        and_gate = schematics.get_schematic("AND")        
        self.assert_2_in_1_out(and_gate, lambda a, b: a and b)

    def test_or(self):
        or_gate = schematics.get_schematic("OR")
        self.assert_2_in_1_out(or_gate, lambda a, b: a or b)

    def test_nor(self):
        nor_gate = schematics.get_schematic("NOR")
        self.assert_2_in_1_out(nor_gate, lambda a, b: not(a or b))

    def test_xor(self):
        xor_gate = schematics.get_schematic("XOR")
        self.assert_2_in_1_out(xor_gate, lambda a, b: a ^ b)

    def test_half_adder(self):
        half_adder = schematics.get_schematic("HALF_ADDER")
        self.assertEqual(len(half_adder.inputs), 2)
        inputs = list(half_adder.inputs.keys())
        input_a = inputs[0]
        input_b = inputs[1]
        
        self.assertEqual(len(half_adder.outputs), 2)
        outputs = list(half_adder.outputs.keys())
        sum_output = outputs[0]
        carry_output = outputs[1]

        possible_inputs = list(product([True, False], repeat=2))
        # +(True) = 1, +(False) = 0
        addition = [+(a) + (+b) for (a, b) in possible_inputs]
        # Pour : a=True, b=False -> sum=0b01 -> bit=sum&1=1, carry=(sum>>1)&1=0
        expected_outputs = [(sum & 1, (sum >> 1) & 1) for sum in addition]

        for (a, b), (sum, carry) in zip(possible_inputs, expected_outputs):
            half_adder.reset()
            half_adder.inputs[input_a].state = a
            half_adder.inputs[input_b].state = b
            self.assertTrue(half_adder.simulate(), "Simulation failed")

            sum_result = half_adder.outputs[sum_output].state
            carry_result = half_adder.outputs[carry_output].state
            self.assertEqual((sum_result, carry_result), (sum, carry))


if __name__ == '__main__':
    unittest.main()