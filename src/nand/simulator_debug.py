from typing import List
from nand.circuit import Circuit

from nand.simulator import Simulator
from nand.wire_converter import convert_wires
from nand.optimization_level import OptimizationLevel
from nand.wire_extended_state import WireExtendedState


class SimulatorDebug(Simulator):
    """A simulator using a cautious approach to simulate a circuit."""

    def __init__(self, circuit: Circuit):
        super().__init__(circuit)
        print(f"convert {circuit.name}")
        print(f"input wires before {self._circuit.get_input_wires()}")
        convert_wires(self._circuit, OptimizationLevel.DEBUG)
        print(f"input wires after {self._circuit.get_input_wires()}")

    def _can_simulate(self, circuit: Circuit) -> bool:
        """Check if the circuit can be simulated, i.e. all inputs are determined."""
        return all(
            wire.state != WireExtendedState.UNKNOWN for wire in circuit.get_input_wires()
        )

    def _simulate(self, circuit: Circuit) -> bool:
        """Simulate the circuit.

        The is a "debug" simulation, meaning it can only fails if the circuit
        is incorrect.

        Returns:
            bool: True if simulation completed successfully (all components simulated)
            False if simulation cannot proceed further.
        """
        # If the inputs are not set, we cannot simulate the circuit.
        if not self._can_simulate(circuit):
            print(f"can't simulate: {circuit.name} / {circuit.identifier} : {circuit.get_input_wires()}")
            return False

        # Base case: the circuit is a core gate.
        if self._is_core_gate(circuit):
            self._simulate_core_gate(circuit)
            print("core gate simulated")
            return True

        # Simulate all components.
        # We use a "light" brute-force approach by repeatedly trying to simulate
        # all components. A queue is used to remove from the components already
        # simulated.
        # This approach allows to simulate the circuit even if the components
        # are not defined in topological order.
        components_queue: List[Circuit] = list(circuit.components.values())
        print(f"component queue for circuit {circuit.name} is {components_queue}")
        left = len(components_queue)
        print(f"start: component left: {left}")
        while True:
            to_simulate = left
            for _ in range(to_simulate):
                component = components_queue.pop(0)
                if not self._simulate(component):
                    components_queue.append(component)
            left = len(components_queue)
            print(f"first loop: component left: {left}")

            if to_simulate == left:
                print("all components simulated")
                break

        # If there are still components to simulate, the simulation failed.
        print("not all component simulated")
        return left == 0

    def _reset(self, circuit: Circuit):
        """Reset the wires to a initial UNKNOWN state."""
        for wire in circuit.get_input_wires():
            wire.state = WireExtendedState.UNKNOWN

        for wire in circuit.get_output_wires():
            wire.state = WireExtendedState.UNKNOWN

        for component in circuit.components.values():
            self._reset(component)
