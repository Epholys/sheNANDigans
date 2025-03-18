from typing import Dict, Type

from circuit import Circuit, PortWireDict
from wire import Wire


def convert_wires(circuit: Circuit, wire_class: Type[Wire]):
    _convert_wires_to(circuit, wire_class, {})


def _convert_wires_to(
    circuit: Circuit, wire_class: Type[Wire], new_wires: Dict[int, Wire]
):
    _convert_ports(circuit.inputs, wire_class, new_wires)
    _convert_ports(circuit.outputs, wire_class, new_wires)

    for component in circuit.components.values():
        _convert_wires_to(component, wire_class, new_wires)


def _convert_ports(
    ports: PortWireDict, wire_class: Type[Wire], new_wires: Dict[int, Wire]
):
    for key, existing_wire in list(ports.items()):
        del ports[key]

        if existing_wire.id in new_wires:
            new_wire = new_wires[existing_wire.id]
        else:
            new_wire = wire_class()
            new_wire.state = existing_wire.state
            new_wires[existing_wire.id] = new_wire

        ports[key] = new_wire
