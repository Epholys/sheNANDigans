from typing import Dict, Type

from circuit import Circuit, PortWireDict
from src.optimization_level import OptimizationLevel
from wire import Wire, WireDebug, WireFast


def set_wires(circuit: Circuit, optimization_level: OptimizationLevel):
    match optimization_level:
        case OptimizationLevel.FAST:
            wire_class = WireFast
        case OptimizationLevel.DEBUG:
            wire_class = WireDebug
        case _:
            raise TypeError("Unknown Optimization Level.")
    _set_wires(circuit, wire_class, {})


def _set_wires(circuit: Circuit, wire_class: Type[Wire], new_wires: Dict[int, Wire]):
    circuit.inputs = _set_ports(circuit.inputs, wire_class, new_wires)
    circuit.outputs = _set_ports(circuit.outputs, wire_class, new_wires)

    for component in circuit.components.values():
        _set_wires(component, wire_class, new_wires)


def _set_ports(
    existing_ports: PortWireDict, wire_class: Type[Wire], new_wires: Dict[int, Wire]
) -> PortWireDict:
    new_ports: PortWireDict = {}

    for key, existing_wire in existing_ports.items():
        if existing_wire.id in new_wires:
            new_wire = new_wires[existing_wire.id]
        else:
            new_wire = wire_class()
            new_wires[existing_wire.id] = new_wire

        new_ports[key] = new_wire

    return new_ports
