import functools
import operator
import pytest

from tests.parameters_enums import parameter_ids
from tests.common_test_assertions import (
    assert_basic_gate,
    assert_bitwise_gate,
    assert_mux16,
    assert_mux4way16,
    assert_mux8way16,
    assert_or8,
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
        assert_bitwise_gate(
            simulator=not16,
            gate_logic=lambda inputs: [not (bit) for bit in inputs[0]],
            dimension=16,
            n_ins=1,
        )

    def test_and16(self, simulators):
        and16 = simulators[8]
        assert_bitwise_gate(
            simulator=and16,
            gate_logic=lambda inputs: [a and b for a, b in zip(*inputs)],
            dimension=16,
            n_ins=2,
        )

    def test_or16(self, simulators):
        or16 = simulators[9]
        assert_bitwise_gate(
            simulator=or16,
            gate_logic=lambda inputs: [a or b for a, b in zip(*inputs)],
            dimension=16,
            n_ins=2,
        )

    def test_mux16(self, simulators):
        mux16 = simulators[10]
        assert_mux16(mux16)

    def test_or8(self, simulators):
        or8 = simulators[11]
        assert_or8(or8)

    def test_mux4way16(self, simulators):
        mux4way16 = simulators[12]
        assert_mux4way16(mux4way16)

    @pytest.mark.slow
    def test_mux8way16(self, simulators):
        mux8way16 = simulators[13]
        assert_mux8way16(mux8way16)
