import random
from itertools import product

import pytest

from tests.numeric_operations import bools_to_int
from tests.parameters_enums import Project, parameter_ids
from tests.simulators_factory import build_simulators_cases


def bools_to_signed_int(bits: list[bool]) -> int:
    """Convert a little-endian list of booleans (two's complement) into a signed int."""
    n = len(bits)
    if n == 0:
        raise ValueError("Empty bit list")

    # Build the unsigned value
    value = sum((1 << i) for i, bit in enumerate(bits) if bit)

    # Check the sign bit (most significant bit)
    sign_bit = 1 << (n - 1)
    if value & sign_bit:
        # Negative number: subtract 2^n
        value -= (1 << n)

    return value


@pytest.fixture(scope="module")
def generate_cases(seed: int = 0, n_random_ins: int = 3,) -> list[list[bool]]:
    input_list: list[list[bool]] = []
    input_list.append([True for _ in range(16)])
    input_list.append([False for _ in range(16)])
    input_list.append([True if i % 2 else False for i in range(16)])
    input_list.append([False if i % 2 else True for i in range(16)])
    input_list.append([False if i % 2 else True for i in range(16)])
    input_list.append([True if i % 3 else False for i in range(16)])

    # Random inputs value. Deterministic using a seed.
    random.seed(seed)
    for _ in range(n_random_ins):
        input_list.append([bool(random.randint(0, 1)) for _ in range(16)])

    cases = []
    for x, y in product(input_list, repeat=2):
        cases.append(x + y)

    return cases

@pytest.mark.parametrize(
    "simulators",
    build_simulators_cases(Project.NAND2TETRIS_HACK),
    indirect=["simulators"],
    ids=parameter_ids,
)
class TestHackALU:
    @staticmethod
    def extract_result(result: list[bool])->tuple[list[bool], bool, bool]:
        return result[0:16], result[16], result[17]

    def test_zero(self, simulators, generate_cases: list[list[bool]]):
        alu = simulators[25]

        # out(x, y) = 0
        zx = [True]
        nx = [False]
        zy = [True]
        ny = [False]
        f = [True]
        no = [False]

        for case in generate_cases:
            case = case + zx + nx + zy + ny + f + no

            result = alu.simulate(case)

            if not result:
                assert False, "Simulation Failed"

            out, zr, ng = self.extract_result(result)

            expected_out = 0
            assert bools_to_int(out) == expected_out
            assert zr
            assert not ng

    def test_one(self, simulators, generate_cases: list[list[bool]]):
        alu = simulators[25]

        # out(x, y) = 1
        zx = [True]
        nx = [True]
        zy = [True]
        ny = [True]
        f = [True]
        no = [True]

        for case in generate_cases:
            case = case + zx + nx + zy + ny + f + no

            result = alu.simulate(case)

            if not result:
                assert False, "Simulation Failed"

            out, zr, ng = self.extract_result(result)

            expected_out = 1
            assert bools_to_int(out) == expected_out
            assert not zr
            assert not ng

    def test_negative_one(
        self, simulators, generate_cases: list[list[bool]]
    ):
        alu = simulators[25]

        # out(x, y) = -1
        zx = [True]
        nx = [True]
        zy = [True]
        ny = [False]
        f = [True]
        no = [False]

        for case in generate_cases:
            case = case + zx + nx + zy + ny + f + no

            result = alu.simulate(case)

            if not result:
                assert False, "Simulation Failed"

            out, zr, ng = self.extract_result(result)

            expected_out = -1
            assert bools_to_signed_int(out) == expected_out
            assert not zr
            assert ng