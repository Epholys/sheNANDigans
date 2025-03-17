from concurrent.futures import ProcessPoolExecutor
from functools import partial
from itertools import product
import multiprocessing
from typing import Callable, List

import pytest
from src.circuit import Circuit, Tuple
from src.decoding import CircuitDecoder
from src.encoding import CircuitEncoder
from src.schematics import Schematics, SchematicsBuilder


class NumericOperations:
    def __init__(
        self,
        inputs_to_numbers: Callable[[List[bool]], List[int]],
        number_to_outputs: Callable[[int], List[bool]],
        operation: Callable[[List[int]], int],
    ):
        self.inputs_to_numbers = inputs_to_numbers
        self.number_to_outputs = number_to_outputs
        self.operation = operation

    def apply(self, inputs: Tuple[bool, ...]) -> List[bool]:
        input_numbers = self.inputs_to_numbers(list(inputs))
        operation_result = self.operation(input_numbers)
        expected_outputs = self.number_to_outputs(operation_result)
        return expected_outputs


def assert_simulation(data):
    circuit: Circuit
    n_inputs: int
    n_outputs: int
    operations: NumericOperations
    circuit_inputs: Tuple[bool, ...]
    circuit, n_inputs, n_outputs, operations, circuit_inputs = data

    circuit.reset()

    assert len(circuit.inputs) == n_inputs
    input_wires = list(circuit.inputs.values())

    assert len(circuit.outputs) == n_outputs
    output_wires = list(circuit.outputs.values())

    expected_outputs = operations.apply(circuit_inputs)

    for input_wire, input in zip(input_wires, circuit_inputs):
        input_wire.state = input

    assert circuit.simulate(), "Simulation failed"

    actual_outputs = [bool(wire.state) for wire in output_wires]
    assert actual_outputs == expected_outputs


class TestedCircuits:
    reference_circuits: Schematics | None = None
    round_trip_circuits: Schematics | None = None
    reference_circuits_debug: Schematics | None = None
    round_trip_circuits_debug: Schematics | None = None


tested_circuits = TestedCircuits()


def build_circuits(processing: str, debug: bool):
    global tested_circuits

    if not debug:
        if tested_circuits.reference_circuits is None:
            builder = SchematicsBuilder()
            builder.build_circuits()
            tested_circuits.reference_circuits = builder.schematics
        if processing == "round_trip" and tested_circuits.round_trip_circuits is None:
            encoded = CircuitEncoder(tested_circuits.reference_circuits).encode()
            tested_circuits.round_trip_circuits = CircuitDecoder(encoded).decode()
    else:
        if tested_circuits.reference_circuits_debug is None:
            builder = SchematicsBuilder(debug=True)
            builder.build_circuits()
            tested_circuits.reference_circuits_debug = builder.schematics
        if (
            processing == "round_trip"
            and tested_circuits.round_trip_circuits_debug is None
        ):
            encoded = CircuitEncoder(tested_circuits.reference_circuits_debug).encode()
            tested_circuits.round_trip_circuits_debug = CircuitDecoder(
                encoded, debug=True
            ).decode()


@pytest.fixture(scope="function")
def schematics(request):
    processing, debug = request.param

    global tested_circuits

    build_circuits(processing, debug)

    if processing == "reference":
        if not debug:
            return tested_circuits.reference_circuits
        else:
            return tested_circuits.reference_circuits_debug
    elif processing == "round_trip":
        if not debug:
            return tested_circuits.round_trip_circuits
        else:
            return tested_circuits.round_trip_circuits_debug
    else:
        return None


@pytest.mark.parametrize(
    "schematics",
    [
        pytest.param(("reference", False)),
        pytest.param(("round_trip", False)),
        pytest.param(("reference", True), marks=pytest.mark.debug),
        pytest.param(("round_trip", True), marks=pytest.mark.debug),
    ],
    indirect=["schematics"],
)
class TestSchematics:
    def assert_2_in_1_out(
        self, gate: Circuit, gate_logic: Callable[[bool, bool], bool]
    ):
        assert len(gate.inputs) == 2
        inputs = list(gate.inputs.values())
        input_a = inputs[0]
        input_b = inputs[1]

        assert len(gate.outputs) == 1
        output = list(gate.outputs.values())[0]

        possible_inputs = list(product([True, False], repeat=2))
        expected_outputs = [gate_logic(a, b) for a, b in possible_inputs]

        for (a, b), expected_output in zip(possible_inputs, expected_outputs):
            gate.reset()
            input_a.state = a
            input_b.state = b
            assert gate.simulate()
            assert bool(output.state) == expected_output

    def test_nand(self, schematics):
        nand_gate = schematics.get_schematic_idx(0)
        self.assert_2_in_1_out(nand_gate, lambda a, b: not (a and b))

    def test_not(self, schematics):
        not_gate = schematics.get_schematic_idx(1)

        assert len(not_gate.inputs) == 1
        input = list(not_gate.inputs.values())[0]

        assert len(not_gate.outputs) == 1
        output = list(not_gate.outputs.values())[0]

        for a in [True, False]:
            not_gate.reset()
            input.state = a
            assert not_gate.simulate()
            assert bool(output.state) == (not a)

    def test_and(self, schematics):
        and_gate = schematics.get_schematic_idx(2)
        self.assert_2_in_1_out(and_gate, lambda a, b: a and b)

    def test_or(self, schematics):
        or_gate = schematics.get_schematic_idx(3)
        self.assert_2_in_1_out(or_gate, lambda a, b: a or b)

    def test_nor(self, schematics):
        nor_gate = schematics.get_schematic_idx(4)
        self.assert_2_in_1_out(nor_gate, lambda a, b: not (a or b))

    def test_xor(self, schematics):
        xor_gate = schematics.get_schematic_idx(5)
        self.assert_2_in_1_out(xor_gate, lambda a, b: a ^ b)

    def assert_numeric_operations(
        self,
        circuit: Circuit,
        n_inputs: int,
        n_outputs: int,
        operations: NumericOperations,
    ):
        all_possible_inputs = list(product([True, False], repeat=n_inputs))

        cases = [
            (circuit, n_inputs, n_outputs, operations, inputs)
            for inputs in all_possible_inputs
        ]

        if n_inputs >= 16:
            n_tasks = len(cases)

            # This is based on almost nothing (well with hyperfine on a ~5s task).
            # There's a big difference between Windows (5.5s) and WSL (3.6s).
            # I know it's because of how the threads/processes are managed between different OSes.
            # I try quickly asking LLMs (2025-03-14 : GPT-4o and Claude 3.7), but they have different opinions.
            # When I profile with 'python -m cProfile', on both OSes it seems that the hyper-parameters of workers and chunks are not optimized:
            # the process management takes the biggest amount of time (Windows's '_winapi.WaitForMultipleObjects' and WSL's 'select.poll').
            # I'll come back later, when I have more tests and more motivation to go deeper on this subject.
            # Things I know (now) that I can try:
            # - Automated hyper-parameters tuning
            # - psutil library
            # - 'multiprocessing.Pool'
            # - loky's 'joblib.Parallel'
            # - Persistent worker pool 'multiprocessing.Pool'
            # - Persistent workers (probably a good idea when I'll have more parallelizable tests)
            # - Different chunking approach: not in 'executor.map(chunksize=)' but pre-chunking: 'chunks=[cases[i+chunk_size] for i in range(len(cases), chunk_size)]'
            # - Analyze pickling
            cpu_count = multiprocessing.cpu_count()
            n_processes = cpu_count - 1
            chunk_size = max(1, n_tasks // (n_processes * 4))

            with ProcessPoolExecutor(max_workers=n_processes) as executor:
                results = list(
                    executor.map(
                        assert_simulation,
                        cases,
                        chunksize=chunk_size,
                    )
                )
            assert len(results) == n_tasks

        else:
            for case in cases:
                assert_simulation(case)

    def test_half_adder(self, schematics):
        half_adder = schematics.get_schematic_idx(6)

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

        self.assert_numeric_operations(
            half_adder,
            2,
            2,
            NumericOperations(inputs_to_numbers, number_to_output, sum),
        )

    def test_full_adder(self, schematics):
        full_adder = schematics.get_schematic_idx(7)

        # Inputs : a, b, cin
        # Operation : a + b + cin
        # Output : sum, cout
        # Ex: a=1, b=0, cin=1 / 1 + 0 + 1 = 2 = 0b10 / sum:0, cout:1

        n_inputs = 3
        n_outputs = 2

        def inputs_to_numbers(inputs: List[bool]):
            assert len(inputs) == n_inputs
            return [+(b) for b in inputs]

        self.assert_numeric_operations(
            full_adder,
            n_inputs,
            n_outputs,
            NumericOperations(
                inputs_to_numbers,
                number_to_outputs=lambda n: int_to_bools(n, n_outputs),
                operation=sum,
            ),
        )

    def test_2bits_adder(self, schematics):
        two_bits_adder = schematics.get_schematic_idx(8)

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

        self.assert_numeric_operations(
            two_bits_adder,
            n_inputs,
            n_outputs,
            NumericOperations(
                inputs_to_numbers,
                number_to_outputs=lambda n: int_to_bools(n, n_outputs),
                operation=sum,
            ),
        )

    def test_4bits_adder(self, schematics):
        four_bits_adder = schematics.get_schematic_idx(9)

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

        self.assert_numeric_operations(
            four_bits_adder,
            n_inputs,
            n_outputs,
            NumericOperations(
                inputs_to_numbers,
                number_to_outputs=lambda n: int_to_bools(n, n_outputs),
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
    def test_8bits_adder(self, schematics):
        eight_bits_adder = schematics.get_schematic_idx(10)

        # See other adders

        n_inputs = 17
        n_outputs = 9

        self.assert_numeric_operations(
            eight_bits_adder,
            n_inputs,
            n_outputs,
            NumericOperations(
                self.eight_bits_inputs_to_numbers,
                number_to_outputs=int_to_bools_partial(n_outputs),
                operation=sum,
            ),
        )


def bools_to_int(bools: List[bool]):
    """
    bools from low to high
    """
    return sum(b * (2**n) for n, b in enumerate(bools))


def int_to_bools_partial(n: int) -> Callable[[int], List[bool]]:
    return partial(int_to_bools, n=n)


def int_to_bools(x: int, n: int) -> List[bool]:
    """
    bools from low to high
    """
    return [(x >> shift) & 1 > 0 for shift in range(n)]
