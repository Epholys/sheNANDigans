
from nand.circuit import Circuit, CircuitId

type CoreCircuits = list[tuple[CircuitId, Circuit]]

def flatten_circuit(circuit: Circuit) -> Circuit:
    """Extract all connections from and to circuit inputs/outputs and components'
    core gates.
    """

    _, all_cores = _explore_circuit_recursive(circuit)

    flattened_circuit = Circuit(circuit.identifier)

    for identifier, core in all_cores:
        flattened_circuit.add_component(identifier, core)

    flattened_circuit.inputs = circuit.inputs
    flattened_circuit.inputs_names = circuit.inputs_names
    flattened_circuit.outputs = circuit.outputs
    flattened_circuit.outputs_names = circuit.outputs_names

    return flattened_circuit


def _explore_circuit_recursive(
    circuit: Circuit,
        counter: int = 0,
) -> tuple[int, CoreCircuits]:
    """Recursively explore the circuit to extract all core gates."""
    all_cores: CoreCircuits = []

    # Process all components in this circuit
    for component in circuit.components.values():
        match component.identifier:
            case 0:  # NAND gate
                all_cores.append((counter, component))
                counter += 1
            case 1:  # ZERO gate
                all_cores.append((counter, component))
                counter += 1
            case 2:  # ONE gate
                all_cores.append((counter, component))
                counter += 1
            case _:
                # Recursively process nested circuit
                new_counter, cores = _explore_circuit_recursive(component, counter)
                counter = new_counter
                all_cores.extend(cores)

    return counter, all_cores
