from typing import Dict, Type

from nand.circuit import Circuit, PortWireDict
from nand.optimization_level import OptimizationLevel
from nand.wire_bundle import WireBundle
from nand.wire_debug import WireDebug
from nand.wire_fast import WireFast
from nand.wire import Wire


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

    print(f"inputs wire before converted: {[repr(wire) for wire in circuit.get_input_wires()]}")

    _convert_wires(circuit, wire_class, {})

    print(f"inputs wire converted: {[repr(wire) for wire in circuit.get_input_wires()]}")


def _convert_wires(
    circuit: Circuit, wire_class: Type[Wire], new_wires: Dict[int, WireBundle]
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
    existing_bundles: PortWireDict, wire_class: Type[Wire], new_bundles: Dict[int, WireBundle]
):
    """Convert the ports dictionary of a circuit to a new wire class.

    Args:
        existing_bundles: The existing ports dictionary to convert. # TODO "existing"?
        wire_class: The class of the wire to convert to.
        new_bundles: The dictionary of new wires to keep the circuit connections.
    """
    print("---")
    print(f"existing bundles: {[repr(wire) for bundle in existing_bundles.values() for wire in bundle.wires]}")
    for key, existing_bundle in list(existing_bundles.items()):
        if existing_bundle.id in new_bundles:
            print("new bundle exist")
            new_bundle = new_bundles[existing_bundle.id]
        else:
            print("new new bundle")
            new_wires = [wire_class() for _ in range(existing_bundle.size)]
            new_bundle = WireBundle(existing_bundle.size)
            new_bundle.wires = new_wires
            new_bundles[existing_bundle.id] = new_bundle

        print(f"key: {repr(key)}")
        print(f"existing bundle [key] = {existing_bundles[key].id}")
        print(f"existing bundle [key] wires = {[repr(wire) for wire in existing_bundles[key].wires]})")
        print(f"new bundle [key] = {new_bundle.id}")
        print(f"new bundle [key] wires = {[repr(wire) for wire in new_bundle.wires]}")


        existing_bundles[key] = new_bundle
