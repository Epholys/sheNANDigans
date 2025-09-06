import pytest

from tests.parameters_enums import parameter_ids
from tests.common_test_assertions import assert_logic_gate_simulations
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
        assert_logic_gate_simulations(nand, lambda a, b: not (a and b))

    def test_not(self, simulators):
        not_ = simulators[1]

        tttassert(not_, lambda in_: not in_, 1)

    def test_and(self, simulators):
        and_ = simulators[2]
        assert_logic_gate_simulations(and_, lambda a, b: a and b)

    def test_or(self, simulators):
        or_ = simulators[3]
        assert_logic_gate_simulations(or_, lambda a, b: a or b)

    def test_xor(self, simulators):
        xor = simulators[4]
        assert_logic_gate_simulations(xor, lambda a, b: a ^ b)

    def test_mux(self, simulators):
        mux = simulators[5]
        tttassert(mux, lambda sel, a, b: b if sel else a, 3)
