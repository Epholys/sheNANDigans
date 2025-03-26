from typing import Dict, Type

from circuit import Circuit, PortWireDict
from optimization_level import OptimizationLevel
from src.wire_debug import WireDebug
from src.wire_fast import WireFast
from wire import Wire


def convert_wires(circuit: Circuit, optimization_level: OptimizationLevel):
    """Convert the wires of a circuit to a wire class based on the optimization level.

    Args:
        circuit: The circuit to convert.
        optimization_level: The optimization level to select the appropriate wire class.
    """
    match optimization_level:
        case OptimizationLevel.FAST:
            wire_class = WireFast
        case OptimizationLevel.DEBUG:
            wire_class = WireDebug
        case _:
            raise ValueError("Unknown Optimization Level.")

    _convert_wires(circuit, wire_class, {})


def _convert_wires(
    circuit: Circuit, wire_class: Type[Wire], new_wires: Dict[int, Wire]
):
    """Recursively convert the wires of a circuit to a new wire class.

    Args:
        circuit: The circuit to convert.
        wire_class: The class of the wire to convert to.
        new_wires: The dictionary of new wires, transmitted recursively,
        to keep the circuit connections.
    """
    _convert_ports(circuit.inputs, wire_class, new_wires)
    _convert_ports(circuit.outputs, wire_class, new_wires)

    for component in circuit.components.values():
        _convert_wires(component, wire_class, new_wires)


def _convert_ports(
    existing_wires: PortWireDict, wire_class: Type[Wire], new_wires: Dict[int, Wire]
):
    """Convert the ports dictionary of a circuit to a new wire class.

    Args:
        existing_ports: The existing ports dictionary to convert.
        wire_class: The class of the wire to convert to.
        new_wires: The dictionary of new wires to keep the circuit connections.
    """
    for key, existing_wire in list(existing_wires.items()):
        if existing_wire.id in new_wires:
            new_wire = new_wires[existing_wire.id]
        else:
            new_wire = wire_class()
            new_wires[existing_wire.id] = new_wire

        existing_wires[key] = new_wire
