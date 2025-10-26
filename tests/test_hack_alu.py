import random
from itertools import product
from typing import Callable

import pytest

from nand.simulator import Simulator
from tests.numeric_operations import bools_to_int
from tests.parameters_enums import Project, parameter_ids
from tests.simulators_factory import build_simulators_cases


def bools2sint(bits: list[bool]) -> int:
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
        value -= 1 << n

    return value


def to_signed16(n: int) -> int:
    """Wrap integer n to 16-bit signed range."""
    n &= 0xFFFF  # keep only the low 16 bits
    if n >= 0x8000:
        n -= 0x10000  # convert to negative range
    return n


@pytest.fixture(scope="module")
def cases(
    seed: int = 0,
    n_random_ins: int = 3,
) -> list[list[bool]]:
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


def simulate_operation(
    simulators: list[Simulator],
    cases: list[list[bool]],
    flags: list[bool],
    assertions: Callable[[list[bool], bool, bool, list[bool]], None],
) -> None:
    alu = simulators[25]

    for case in cases:
        case = case + flags
        result = alu.simulate(case)

        if not result:
            assert False, "Simulation Failed"

        out, zr, ng = extract_result(result)

        assertions(out, zr, ng, case)


def extract_result(result: list[bool]) -> tuple[list[bool], bool, bool]:
    return result[0:16], result[16], result[17]


@pytest.mark.parametrize(
    "simulators",
    build_simulators_cases([Project.NAND2TETRIS_HACK,
                            #Project.NAND2TETRIS_HACK_FLATTENED]
                            ]),
    indirect=["simulators"],
    ids=parameter_ids,
)
class TestHackALU:
    def test_zero(self, simulators, cases):
        # out(x, y) = 0
        zx = [True]
        nx = [False]
        zy = [True]
        ny = [False]
        f = [True]
        no = [False]

        def assert_zero(out: list[bool], zr: bool, ng: bool, _):
            expected_out = 0
            assert bools_to_int(out) == expected_out
            assert zr
            assert not ng

        simulate_operation(simulators, cases, zx + nx + zy + ny + f + no, assert_zero)

    def test_one(self, simulators, cases):
        # out(x, y) = 1
        zx = [True]
        nx = [True]
        zy = [True]
        ny = [True]
        f = [True]
        no = [True]

        def assert_one(out: list[bool], zr: bool, ng: bool, _):
            expected_out = 1
            assert bools_to_int(out) == expected_out
            assert not zr
            assert not ng

        simulate_operation(simulators, cases, zx + nx + zy + ny + f + no, assert_one)

    def test_negative_one(self, simulators, cases):
        # out(x, y) = -1
        zx = [True]
        nx = [True]
        zy = [True]
        ny = [False]
        f = [True]
        no = [False]

        def assert_negative_one(out: list[bool], zr: bool, ng: bool, _):
            expected_out = -1
            assert bools2sint(out) == expected_out
            assert not zr
            assert ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_negative_one
        )

    def test_x(self, simulators, cases):
        # out(x, y) = x
        zx = [False]
        nx = [False]
        zy = [True]
        ny = [True]
        f = [False]
        no = [False]

        def assert_x(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            x = bools2sint(case[0:16])
            assert bools2sint(out) == x
            assert zr if x == 0 else not zr
            assert ng if x < 0 else not ng

        simulate_operation(simulators, cases, zx + nx + zy + ny + f + no, assert_x)

    def test_y(self, simulators, cases):
        # out(x, y) = y
        zx = [True]
        nx = [True]
        zy = [False]
        ny = [False]
        f = [False]
        no = [False]

        def assert_y(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            y = bools2sint(case[16:32])
            assert bools2sint(out) == y
            assert zr if y == 0 else not zr
            assert ng if y < 0 else not ng

        simulate_operation(simulators, cases, zx + nx + zy + ny + f + no, assert_y)

    def test_not_x(self, simulators, cases):
        # out(x, y) = !x
        zx = [False]
        nx = [False]
        zy = [True]
        ny = [True]
        f = [False]
        no = [True]

        def assert_not_x(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            not_x = [not b for b in case[0:16]]
            not_x_int = bools2sint(not_x)
            assert out == not_x
            assert zr if not_x_int == 0 else not zr
            assert ng if not_x_int < 0 else not ng

        simulate_operation(simulators, cases, zx + nx + zy + ny + f + no, assert_not_x)

    def test_not_y(self, simulators, cases):
        # out(x, y) = !y
        zx = [True]
        nx = [True]
        zy = [False]
        ny = [False]
        f = [False]
        no = [True]

        def assert_not_y(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            not_y = [not b for b in case[16:32]]
            not_y_int = bools2sint(not_y)
            assert out == not_y
            assert zr if not_y_int == 0 else not zr
            assert ng if not_y_int < 0 else not ng

        simulate_operation(simulators, cases, zx + nx + zy + ny + f + no, assert_not_y)

    def test_minus_x(self, simulators, cases):
        # out(x, y) = -x
        zx = [False]
        nx = [False]
        zy = [True]
        ny = [True]
        f = [True]
        no = [True]

        def assert_minus_x(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            minus_x = -bools2sint(case[0:16])
            assert bools2sint(out) == minus_x
            assert zr if minus_x == 0 else not zr
            assert ng if minus_x < 0 else not ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_minus_x
        )

    def test_minus_y(self, simulators, cases):
        # out(x, y) = -y
        zx = [True]
        nx = [True]
        zy = [False]
        ny = [False]
        f = [True]
        no = [True]

        def assert_minus_y(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            minus_y = -bools2sint(case[16:32])
            assert bools2sint(out) == minus_y
            assert zr if minus_y == 0 else not zr
            assert ng if minus_y < 0 else not ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_minus_y
        )

    def test_x_plus_one(self, simulators, cases):
        # out(x, y) = x + 1
        zx = [False]
        nx = [True]
        zy = [True]
        ny = [True]
        f = [True]
        no = [True]

        def assert_x_plus_one(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            x_plus_one = bools2sint(case[0:16]) + 1
            assert bools2sint(out) == x_plus_one
            assert zr if x_plus_one == 0 else not zr
            assert ng if x_plus_one < 0 else not ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_x_plus_one
        )

    def test_y_plus_one(self, simulators, cases):
        # out(x, y) = y + 1
        zx = [True]
        nx = [True]
        zy = [False]
        ny = [True]
        f = [True]
        no = [True]

        def assert_y_plus_one(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            y_plus_one = bools2sint(case[16:32]) + 1
            assert bools2sint(out) == y_plus_one
            assert zr if y_plus_one == 0 else not zr
            assert ng if y_plus_one < 0 else not ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_y_plus_one
        )

    def test_x_minus_one(self, simulators, cases):
        # out(x, y) = x - 1
        zx = [False]
        nx = [False]
        zy = [True]
        ny = [True]
        f = [True]
        no = [False]

        def assert_x_minus_one(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            x_minus_one = bools2sint(case[0:16]) - 1
            assert bools2sint(out) == x_minus_one
            assert zr if x_minus_one == 0 else not zr
            assert ng if x_minus_one < 0 else not ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_x_minus_one
        )

    def test_y_minus_one(self, simulators, cases):
        # out(x, y) = y - 1
        zx = [True]
        nx = [True]
        zy = [False]
        ny = [False]
        f = [True]
        no = [False]

        def assert_y_minus_one(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            y_minus_one = bools2sint(case[16:32]) - 1
            assert bools2sint(out) == y_minus_one
            assert zr if y_minus_one == 0 else not zr
            assert ng if y_minus_one < 0 else not ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_y_minus_one
        )

    def test_x_plus_y(self, simulators, cases):
        # out(x, y) = x + y
        zx = [False]
        nx = [False]
        zy = [False]
        ny = [False]
        f = [True]
        no = [False]

        def assert_x_plus_y(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            x = bools2sint(case[0:16])
            y = bools2sint(case[16:32])
            res = to_signed16(x + y)
            assert bools2sint(out) == res
            assert zr if res == 0 else not zr
            assert ng if res < 0 else not ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_x_plus_y
        )

    def test_x_minus_y(self, simulators, cases):
        # out(x, y) = x - y
        zx = [False]
        nx = [True]
        zy = [False]
        ny = [False]
        f = [True]
        no = [True]

        def assert_x_minus_y(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            x = bools2sint(case[0:16])
            y = bools2sint(case[16:32])
            res = to_signed16(x - y)
            assert bools2sint(out) == res
            assert zr if res == 0 else not zr
            assert ng if res < 0 else not ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_x_minus_y
        )

    def test_y_minus_x(self, simulators, cases):
        # out(x, y) = y - x
        zx = [False]
        nx = [False]
        zy = [False]
        ny = [True]
        f = [True]
        no = [True]

        def assert_y_minus_x(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            x = bools2sint(case[0:16])
            y = bools2sint(case[16:32])
            res = to_signed16(y - x)
            assert bools2sint(out) == res
            assert zr if res == 0 else not zr
            assert ng if res < 0 else not ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_y_minus_x
        )

    def test_x_and_y(self, simulators, cases):
        # out(x, y) = x & y
        zx = [False]
        nx = [False]
        zy = [False]
        ny = [False]
        f = [False]
        no = [False]

        def assert_x_and_y(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            x = case[0:16]
            y = case[16:32]
            res = [x & y for x, y in zip(x, y)]
            res_int = bools2sint(res)
            assert out == res
            assert zr if res_int == 0 else not zr
            assert ng if res_int < 0 else not ng

        simulate_operation(
            simulators, cases, zx + nx + zy + ny + f + no, assert_x_and_y
        )

    def test_x_or_y(self, simulators, cases):
        # out(x, y) = x | y
        zx = [False]
        nx = [True]
        zy = [False]
        ny = [True]
        f = [False]
        no = [True]

        def assert_x_or_y(out: list[bool], zr: bool, ng: bool, case: list[bool]):
            x = case[0:16]
            y = case[16:32]
            res = [x | y for x, y in zip(x, y)]
            res_int = bools2sint(res)
            assert out == res
            assert zr if res_int == 0 else not zr
            assert ng if res_int < 0 else not ng

        simulate_operation(simulators, cases, zx + nx + zy + ny + f + no, assert_x_or_y)
