from typing import List

import pytest
from tests.parameters_enums import parameter_ids
from tests.common_gate_assertions import (
    assert_basic_gate,
)
from tests.numeric_operations import (
    NumericOperations,
    bools_to_int,
    int_to_bools,
)
from tests.simulators_factory import Project, build_simulators_cases
from tests.common_numeric_assertions import assert_all_numeric_simulations


@pytest.mark.parametrize(
    "simulators",
    build_simulators_cases(Project.PLAYGROUND),
    indirect=["simulators"],
    ids=parameter_ids,
)
class TestPlaygroundLibrary:
    """Test the circuits behavior on the different cases.

    The goal is to test
    - The reference circuits (implemented in python) vs the round-trip circuits (going
    through encoding and decoding).
    - The different simulators with optimization levels (fast vs debug).

    TODO: add better error message for numeric simulations
    TODO: even maybe merge them in common_test_assertion
    """

    def test_nand(self, simulators):
        nand = simulators[0]
        assert_basic_gate(nand, lambda a, b: not (a and b))

    def test_not(self, simulators):
        not_ = simulators[1]

        for a in [True, False]:
            result = not_.simulate([a])
            if not result:
                assert False, "Simulation Failed"
            assert result == [not a]

    def test_and(self, simulators):
        and_ = simulators[2]
        assert_basic_gate(and_, lambda a, b: a and b)

    def test_or(self, simulators):
        or_ = simulators[3]
        assert_basic_gate(or_, lambda a, b: a or b)

    def test_nor(self, simulators):
        nor = simulators[4]
        assert_basic_gate(nor, lambda a, b: not (a or b))

    def test_xor(self, simulators):
        xor = simulators[5]
        assert_basic_gate(xor, lambda a, b: a ^ b)

    def test_half_adder(self, simulators):
        half_adder = simulators[6]

        # Inputs : a, b
        # Operation : a + b
        # Output : sum, carry
        # Ex: a=1, b=0 / 1 + 0 = 2 = 0b01 / sum:1, carry:0

        def inputs_to_numbers(inputs: List[bool]):
            assert len(inputs) == 2
            return [+(b) for b in inputs]

        def number_to_output(number: int):
            sum = number & 1
            carry = (number >> 1) & 1
            return [bool(x) for x in [sum, carry]]

        assert_all_numeric_simulations(
            half_adder,
            2,
            2,
            NumericOperations(inputs_to_numbers, number_to_output, sum),
        )

    def test_full_adder(self, simulators):
        full_adder = simulators[7]

        # Inputs : a, b, cin
        # Operation : a + b + cin
        # Output : sum, cout
        # Ex: a=1, b=0, cin=1 / 1 + 0 + 1 = 2 = 0b10 / sum:0, cout:1

        n_inputs = 3
        n_outputs = 2

        def inputs_to_numbers(inputs: List[bool]):
            assert len(inputs) == n_inputs
            return [+(b) for b in inputs]

        assert_all_numeric_simulations(
            full_adder,
            n_inputs,
            n_outputs,
            NumericOperations(
                inputs_to_numbers,
                number_to_outputs=int_to_bools(n_outputs),
                operation=sum,
            ),
        )

    def test_2bits_adder(self, simulators):
        two_bits_adder = simulators[8]

        # Inputs : a0, b0, c0, a1, b1
        # Outputs: s0, s1, cout
        # Input Numbers  : A = 0b_a1_a0 ; B = 0b_b1_b0 ; Carry = c0
        # Output Numbers : S = 0b_cout_s1_s0
        # Operation : A + B + Carry = S
        # Ex: a0=1, a1=0, cin=1, b0=0, b1=1
        # A = 0b01 = 1
        # B = 0b10 = 2
        # Carry = 0b1 = 1
        # Operation : 1 + 2 + 1 = 4 = 0b100
        # Outputs = s0=0 ; s1=1 ; cout=1

        n_inputs = 5
        n_outputs = 3

        def inputs_to_numbers(inputs: List[bool]):
            assert len(inputs) == n_inputs

            # a0 a1
            a = [inputs[i] for i in [0, 3]]

            # b0 b1
            b = [inputs[i] for i in [1, 4]]

            c0 = +(inputs[2])

            a = bools_to_int(a)
            b = bools_to_int(b)

            return [a, b, c0]

        assert_all_numeric_simulations(
            two_bits_adder,
            n_inputs,
            n_outputs,
            NumericOperations(
                inputs_to_numbers,
                number_to_outputs=int_to_bools(n_outputs),
                operation=sum,
            ),
        )

    def test_4bits_adder(self, simulators):
        four_bits_adder = simulators[9]

        # Inputs : a0, b0, c0, a1, b1, a2, b2, a3, b3
        # Outputs: s0, s1, s2, s3, cout
        # Input Numbers  : A = 0b_a3_a2_a1_a0 ; B = 0b_b3_b2_b1_b0 ; Carry = c0
        # Output Numbers : S = 0b_cout_s3_s2_s1_s0
        # Operation : A + B + Carry = S
        # Ex: a0=1, a1=0, a2=1, a3=0, cin=0, b0=0, b1=1, b2=1, b3=1
        # A = 0b0101 = 5
        # B = 0b1110 = 14
        # Carry = 0b0 = 0
        # Operation : 5 + 14 + 0 = 19 = 0b01011
        # Outputs = s0=1 ; s1=1, s2=0, s3=1 ; cout=0

        n_inputs = 9
        n_outputs = 5

        def inputs_to_numbers(inputs: List[bool]):
            assert len(inputs) == n_inputs

            # a0 a1 a2 a3
            a = [inputs[i] for i in [0, 3, 5, 7]]

            # b0 b1 b2 b3
            b = [inputs[i] for i in [1, 4, 6, 8]]

            c0 = +(inputs[2])

            a = bools_to_int(a)
            b = bools_to_int(b)

            return [a, b, c0]

        assert_all_numeric_simulations(
            four_bits_adder,
            n_inputs,
            n_outputs,
            NumericOperations(
                inputs_to_numbers,
                number_to_outputs=int_to_bools(n_outputs),
                operation=sum,
            ),
        )

    @staticmethod
    def eight_bits_inputs_to_numbers(inputs: List[bool]):
        # interleaved and c0 : a0 b0 c0 a1 b1 ... a7 b7

        # a0 ... a7
        a_indices: List[int] = [0, *range(3, 16, 2)]
        a = [inputs[i] for i in a_indices]

        # b0 ... b7
        b_indices: List[int] = [1, *range(4, 17, 2)]
        b = [inputs[i] for i in b_indices]

        c0 = +(inputs[2])

        a = bools_to_int(a)
        b = bools_to_int(b)

        return [a, b, c0]

    @pytest.mark.slow
    def test_8bits_adder(self, simulators):
        eight_bits_adder = simulators[10]

        # See other adders

        n_inputs = 17
        n_outputs = 9

        assert_all_numeric_simulations(
            eight_bits_adder,
            n_inputs,
            n_outputs,
            NumericOperations(
                self.eight_bits_inputs_to_numbers,
                number_to_outputs=int_to_bools(n_outputs),
                operation=sum,
            ),
        )
