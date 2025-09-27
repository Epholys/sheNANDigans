from functools import partial
from itertools import batched
import operator
from typing import Sequence
import pytest

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

_mapping = {
    "NAND": 0,
    "ZERO": 1,
    "ONE": 2,
    "NOT": 3,
    "AND": 4,
    "OR": 5,
    "XOR": 6,
    "MUX": 7,
    "DMUX": 8,
    "NOT16": 9,
    "AND16": 10,
    "OR16": 11,
    "MUX16": 12,
    "OR8WAY": 13,
    "MUX4WAY16": 14,
    "MUX8WAY16": 15,
    "DMUX4WAY": 16,
    "DMUX8WAY": 17,
    "HALF_ADDER": 18,
    "FULL_ADDER": 19,
    "ADD16": 20,
}


@pytest.mark.parametrize(
    "simulators",
    build_simulators_cases(Project.NAND2TETRIS_HACK),
    indirect=["simulators"],
    ids=parameter_ids,
)
class TestLibrary:
    # TODO: extract core gates tests in a common test file
    def test_nand(self, simulators):
        nand = simulators[_mapping["NAND"]]
        assert_basic_gate(nand, lambda a, b: not (a and b))

    def test_zero(self, simulators):
        zero = simulators[_mapping["ZERO"]]

        result = zero.simulate([])
        if not result:
            assert False, "Simulation Failed"
        assert result == [False]

    def test_one(self, simulators):
        one = simulators[_mapping["ONE"]]

        result = one.simulate([])
        if not result:
            assert False, "Simulation Failed"
        assert result == [True]

    def test_not(self, simulators):
        not_ = simulators[_mapping["NOT"]]
        assert_basic_gate(not_, lambda in_: not in_, n_in=1)

    def test_and(self, simulators):
        and_ = simulators[_mapping["AND"]]
        assert_basic_gate(and_, lambda a, b: a and b)

    def test_or(self, simulators):
        or_ = simulators[_mapping["OR"]]
        assert_basic_gate(or_, lambda a, b: a or b)

    def test_xor(self, simulators):
        xor = simulators[_mapping["XOR"]]
        assert_basic_gate(xor, lambda a, b: a ^ b)

    def test_mux(self, simulators):
        mux = simulators[_mapping["MUX"]]
        # Input:    a, b, sel
        # Output:   out
        # Function: if (sel == 0) then out = a, else out = b
        assert_basic_gate(mux, lambda a, b, sel: a if not sel else b, n_in=3)

    def test_dmux(self, simulators):
        mux = simulators[_mapping["DMUX"]]
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
        not16 = simulators[_mapping["NOT16"]]
        assert_multibits_gate(
            simulator=not16,
            operation=lambda inputs: [not (bit) for bit in inputs[0]],
            m_bits=16,
            n_ins=1,
        )

    def test_and16(self, simulators):
        and16 = simulators[_mapping["AND16"]]
        assert_multibits_gate(
            simulator=and16,
            operation=lambda inputs: [a and b for a, b in zip(*inputs)],
            m_bits=16,
            n_ins=2,
        )

    def test_or16(self, simulators):
        or16 = simulators[_mapping["OR16"]]
        assert_multibits_gate(
            simulator=or16,
            operation=lambda inputs: [a or b for a, b in zip(*inputs)],
            m_bits=16,
            n_ins=2,
        )

    def test_mux16(self, simulators):
        mux16 = simulators[_mapping["MUX16"]]
        assert_mux_n_way_m_bits(mux16, n_way=2, m_bits=16)

    def test_or8way(self, simulators):
        or8 = simulators[_mapping["OR8WAY"]]
        assert_n_way_gate(or8, operator.or_, n_way=8)

    def test_mux4way16(self, simulators):
        mux4way16 = simulators[_mapping["MUX4WAY16"]]
        assert_mux_n_way_m_bits(mux4way16, n_way=4, m_bits=16)

    def test_mux8way16(self, simulators):
        mux8way16 = simulators[_mapping["MUX8WAY16"]]
        assert_mux_n_way_m_bits(mux8way16, n_way=8, m_bits=16)

    def test_dmux4way(self, simulators):  #
        dmux4way = simulators[_mapping["DMUX4WAY"]]
        assert_dmux_n_way(dmux4way, 4)

    def test_dmux8way(self, simulators):  #
        dmux8way = simulators[_mapping["DMUX8WAY"]]
        assert_dmux_n_way(dmux8way, 8)

    def test_half_adder(self, simulators):
        half_adder = simulators[_mapping["HALF_ADDER"]]

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
        full_adder = simulators[_mapping["FULL_ADDER"]]

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
        add16 = simulators[_mapping["ADD16"]]

        n_inputs = 2
        n_outputs = 1
        n_bits = 16

        # 2 ** 32 is too much for this hilariously not optimized python simulation.
        # So no 'assert_all_numeric_simulations()'

        def bools_to_n_ints(bits: Sequence[bool], n: int) -> list[int]:
            bools_numbers = list(batched(bits, n))
            return [bools_to_int(b) for b in bools_numbers]

        def truncated_sum(numbers: list[int], n_bits: int):
            sum_ = sum(numbers)
            return sum_ % (1 << n_bits)

        assert_partial_numeric_simulation(
            add16,
            n_inputs,
            n_outputs,
            n_bits,
            NumericOperations(
                inputs_to_numbers=partial(bools_to_n_ints, n=n_bits),
                number_to_outputs=int_to_bools(n_bits),
                operation=partial(truncated_sum, n_bits=n_bits),
            ),
        )
