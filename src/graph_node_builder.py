from typing import Dict
import pydot
import seaborn

from circuit import Circuit, CircuitKey


def golden_ratio_generator(scale: int):
    """Generate a sequence of indices based on the golden ratio.

    This generator yields numbers that are evenly spaced on a 0..scale interval.
    """
    phi = (5**0.5 - 1) / 2  # Golden ratio conjugate (~0.618)
    i = 0
    while True:
        yield int(scale * ((i * phi) % 1))
        i += 1


class ColorScheme:
    """A color scheme for circuit components.

    This class generates a color palette for circuit components using the golden ratio.
    It ensures that the colors are evenly spaced and visually distinct.
    """

    # The size of the color palette
    PALETTE_SIZE = 32

    def __init__(self):
        self._colors: Dict[CircuitKey, str] = {}
        self._generator = golden_ratio_generator(self.PALETTE_SIZE)
        self._palette = seaborn.husl_palette(
            n_colors=self.PALETTE_SIZE, s=0.95, l=0.8, h=0.5
        ).as_hex()

    def get_color(self, id: CircuitKey) -> str:
        """Get a color for a given circuit component ID.
        If the color has already been assigned, return the existing color.
        """
        if id in self._colors:
            return self._colors[id]
        color = self._palette[next(self._generator)]
        self._colors[id] = color
        return color


class NodeBuilder:
    """Handles the creation of graph nodes for circuits and components."""

    def __init__(self):
        self.color_scheme = ColorScheme()

    def create_port_node(
        self, graph: pydot.Graph, port_key: CircuitKey, prefix: str, color: str
    ) -> str:
        """Create a node for a circuit port."""
        node_id = f"{prefix}_{port_key}"
        graph.add_node(
            pydot.Node(
                node_id,
                label=f"{port_key}",
                shape="circle",
                style="filled",
                fillcolor=color,
            )
        )
        return node_id

    def create_nand_node(self, graph: pydot.Graph, name: str) -> None:
        """Create a node for a NAND gate."""
        graph.add_node(
            pydot.Node(
                name,
                label="NAND",
                shape="box",
                style="filled",
                fillcolor="#ccccff",
            )
        )

    def create_circuit_node(
        self, graph: pydot.Graph, circuit: Circuit, name: str
    ) -> None:
        """Create a node for a circuit component."""
        graph.add_node(
            pydot.Node(
                name,
                label=circuit.identifier,
                shape="component",
                style="filled",
                fillcolor=self.color_scheme.get_color(circuit.identifier),
            )
        )
