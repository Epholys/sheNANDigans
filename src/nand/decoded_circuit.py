from typing import List, NamedTuple
from nand.circuit import Circuit, CircuitId


class InputParameters(NamedTuple):
    """The parameters to connect a circuit's input

    Values:
        input_index: The index of the input in the circuit.
        component_id: The key of the component to connect the input to.
        component_input_index: The index of the input in the component to connect to.
    """

    input_index: int
    component_id: CircuitId
    component_input_index: int


class ConnectionParameters(NamedTuple):
    """The parameters to connect two components.

    Values:
        source_id: The key of the source component.
        source_output_index: The index of the output in the source component.
        target_id: The key of the target component.
        target_input_index: The index of the input in the target component.
    """

    source_id: CircuitId
    source_output_index: int
    target_id: CircuitId
    target_input_index: int


class DecodedCircuit(Circuit):
    """An intermediate class to decode a circuit.

    It contains information that is not in the Circuit class,
    but is necessary to decode a circuit, or at least to
    check the correctness of the encoded data.

    Attributes:
        n_components: The number of components in the circuit.
        n_inputs: The number of inputs in the circuit.
        n_outputs: The number of outputs in the circuit.
        stashed_inputs: The inputs that are stashed to be connected later.
        stashed_connections: The connections that are stashed to be connected later.
    """

    def __init__(self, identifier: CircuitId):
        super().__init__(identifier)
        self.n_components = 0
        # TODO : unecessary ?
        self.n_inputs = 0
        # TODO : unecessary ?
        self.n_outputs = 0
        self.stashed_inputs: List[InputParameters] = []
        self.stashed_connections: List[ConnectionParameters] = []

    def stash_input(self, input: InputParameters):
        """Stash a circuit's input connection to apply it later."""
        self.stashed_inputs.append(input)

    def apply_inputs(self):
        """Connect the circuit inputs to the corresponding components.

        This connection is deferred until all inputs are decoded. The decoding
        process may encounter circuit inputs out of their intended order.

        Problem:
        If inputs were connected as they are discovered, their order might be
        incorrect. For example, a component's first input might be connected to
        the yet unseen circuit's fourth input (C3), and its second input to the
        circuit's yet unseen second input (C1). The decoder would process the C3
        connection before the C1 connection, swapping the circuit's inputs.

        Solution:
        The original index of each circuit input is encoded alongside the
        connection. This allows us to sort all the decoded inputs by their
        intended index before connecting them, ensuring the final circuit is
        correct.
        """
        self.stashed_inputs.sort(key=lambda x: x.input_index)
        for input_connection in self.stashed_inputs:
            self.connect_input(
                input_connection.input_index,
                input_connection.component_id,
                input_connection.component_input_index,
            )

    def stash_connection(self, connection: ConnectionParameters):
        """Stash a connection between two components to apply it later."""
        self.stashed_connections.append(connection)

    def apply_connections(self):
        """Apply the stashed connections.

        This is necessary because a connection can refer to a component not yet decoded.
        As such, we need to stash the connections and apply them later. Otherwise, it's
        impossible to check the existence of the target component' input.
        """
        for connection in self.stashed_connections:
            self.connect(
                connection.source_id,
                connection.source_output_index,
                connection.target_id,
                connection.target_input_index,
            )
