from functools import partial
from itertools import batched
import operator
from typing import Sequence
import pytest

from nand.bits_utils import bits2int
from tests.common_numeric_assertions import (
    assert_all_numeric_simulations,
    assert_partial_numeric_simulation,
)
from tests.numeric_operations import NumericOperations, bools_to_int, int_to_bools
from tests.parameters_enums import parameter_ids
from tests.common_gate_assertions import (
    assert_basic_gate,
    assert_multibits_gate,
    assert_dmux_n_way,
    assert_mux_n_way_m_bits,
    assert_n_way_gate,
)
from tests.simulators_factory import Project, build_simulators_cases


@pytest.mark.parametrize(
    "simulators",
    build_simulators_cases(Project.NAND2TETRIS_HACK),
    indirect=["simulators"],
    ids=parameter_ids,
)
class TestLibrary:
    def test_nand(self, simulators):
        nand = simulators[0]
        assert_basic_gate(nand, lambda a, b: not (a and b))

    def test_not(self, simulators):
        not_ = simulators[1]
        assert_basic_gate(not_, lambda in_: not in_, n_in=1)

    def test_and(self, simulators):
        and_ = simulators[2]
        assert_basic_gate(and_, lambda a, b: a and b)

    def test_or(self, simulators):
        or_ = simulators[3]
        assert_basic_gate(or_, lambda a, b: a or b)

    def test_xor(self, simulators):
        xor = simulators[4]
        assert_basic_gate(xor, lambda a, b: a ^ b)

    def test_mux(self, simulators):
        mux = simulators[5]
        # Input:    a, b, sel
        # Output:   out
        # Function: if (sel == 0) then out = a, else out = b
        assert_basic_gate(mux, lambda a, b, sel: a if not sel else b, n_in=3)

    def test_dmux(self, simulators):
        mux = simulators[6]
        # Input:    in, sel
        # Output:   a, b
        # Function: if (sel == 0) then {a, b} = {in, 0}
        #           else               {a, b} = {0, in}
        assert_basic_gate(
            mux,
            lambda in_, sel: (in_, False) if not sel else (False, in_),
            n_in=2,
            n_out=2,
        )

    def test_not16(self, simulators):
        not16 = simulators[7]
        assert_multibits_gate(
            simulator=not16,
            operation=lambda inputs: [not (bit) for bit in inputs[0]],
            m_bits=16,
            n_ins=1,
        )

    def test_and16(self, simulators):
        and16 = simulators[8]
        assert_multibits_gate(
            simulator=and16,
            operation=lambda inputs: [a and b for a, b in zip(*inputs)],
            m_bits=16,
            n_ins=2,
        )

    def test_or16(self, simulators):
        or16 = simulators[9]
        assert_multibits_gate(
            simulator=or16,
            operation=lambda inputs: [a or b for a, b in zip(*inputs)],
            m_bits=16,
            n_ins=2,
        )

    def test_mux16(self, simulators):
        mux16 = simulators[10]
        assert_mux_n_way_m_bits(mux16, n_way=2, m_bits=16)

    def test_or8way(self, simulators):
        or8 = simulators[11]
        assert_n_way_gate(or8, operator.or_, n_way=8)

    def test_mux4way16(self, simulators):
        mux4way16 = simulators[12]
        assert_mux_n_way_m_bits(mux4way16, n_way=4, m_bits=16)

    def test_mux8way16(self, simulators):
        mux8way16 = simulators[13]
        assert_mux_n_way_m_bits(mux8way16, n_way=8, m_bits=16)

    def test_dmux4way(self, simulators):  #
        dmux4way = simulators[14]
        assert_dmux_n_way(dmux4way, 4)

    def test_dmux8way(self, simulators):  #
        dmux8way = simulators[15]
        assert_dmux_n_way(dmux8way, 8)

    def test_half_adder(self, simulators):
        half_adder = simulators[16]

        n_inputs = 2
        n_outputs = 2
        assert_all_numeric_simulations(
            half_adder,
            n_inputs,
            n_outputs,
            NumericOperations(
                inputs_to_numbers=lambda bools: [+(b) for b in bools],
                number_to_outputs=int_to_bools(n_outputs),
                operation=sum,
            ),
        )

    def test_full_adder(self, simulators):
        full_adder = simulators[17]

        n_inputs = 3
        n_outputs = 2
        assert_all_numeric_simulations(
            full_adder,
            n_inputs,
            n_outputs,
            NumericOperations(
                inputs_to_numbers=lambda bools: [+(b) for b in bools],
                number_to_outputs=int_to_bools(n_outputs),
                operation=sum,
            ),
        )

    def test_add16_adder(self, simulators):
        add16 = simulators[18]

        n_inputs = 2
        n_outputs = 1
        n_bits = 16

        # 2 ** 32 is too much for this hilariously not optimized python simulation.
        # So no 'assert_all_numeric_simulations()'

        def two_complements(bits: Sequence[bool]) -> int:
            print(bits)
            is_negative = bits[0]
            print(is_negative)
            if not is_negative:
                print(bools_to_int(bits[1:]))
                return bools_to_int(bits[1:])
            flipped = list(map(operator.not_, bits[1:]))
            print(flipped)
            print(-(bools_to_int(flipped) + 1))
            return -(bools_to_int(flipped) + 1)

        def truncated_sum(numbers: list[int], n_bits: int):
            sum_ = sum(numbers)
            print(sum_)
            lower_bound = -(2 ** (n_bits - 1))
            upper_bound = (2**n_bits - 1) - 1
            return min(upper_bound, max(lower_bound, sum_))

        assert_partial_numeric_simulation(
            add16,
            n_inputs,
            n_outputs,
            n_bits,
            NumericOperations(
                inputs_to_numbers=lambda bools: [
                    two_complements(number) for number in batched(bools, n_bits)
                ],
                number_to_outputs=int_to_bools(n_bits),
                operation=partial(truncated_sum, n_bits=n_bits),
            ),
        )
