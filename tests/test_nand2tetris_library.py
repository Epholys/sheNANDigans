import pytest

from tests.common_test_assertions import assert_logic_gate_simulations
from tests.simulators_factory import Project, build_parameters


@pytest.mark.parametrize(
    "simulators",
    build_parameters(Project.NAND2TETRIS_HACK),
    indirect=["simulators"],
    # TODO ids=
)
class TestLibrary:
    def test_nand(self, simulators):
        nand = simulators[0]
        assert_logic_gate_simulations(nand, lambda a, b: not (a and b))

    def test_not(self, simulators):
        not_ = simulators[1]

        for a in [True, False]:
            result = not_.simulate([a])
            if not result:
                assert False, "Simulation Failed"
            assert result == [not a]

    def test_and(self, simulators):
        and_ = simulators[2]
        assert_logic_gate_simulations(and_, lambda a, b: a and b)

    def test_or(self, simulators):
        or_ = simulators[3]
        assert_logic_gate_simulations(or_, lambda a, b: a or b)

    def test_xor(self, simulators):
        xor = simulators[4]
        assert_logic_gate_simulations(xor, lambda a, b: a ^ b)
