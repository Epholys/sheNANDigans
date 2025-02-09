from copy import deepcopy
from typing import OrderedDict
import itertools


class Wire:
    _id_iter = itertools.count()

    def __init__(self, state=None):
        self.state = state
        self.id = next(Wire._id_iter)

    def __deepcopy__(self, memo):
        # Create a new Wire instance with the same state but a new unique id
        new_wire = type(self)(self.state)
        memo[id(self)] = new_wire
        return new_wire

    def __repr__(self):
        return f"Wire(id={self.id}, state={self.state})"
    
    def __str__(self):
        bin = "0" if self.state == False else "1" if self.state == True else "X"
        return bin

class Circuit:
    def __init__(self, identifier):
        self.identifier = identifier
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.components = OrderedDict()
        self.miss = 0

    def add_component(self, name, component):
        self.components[name] = component

    def add_input(self, input_name, component_name, component_input_name):        
        if self.components[component_name] is None:
            raise ValueError(f"Component {component_name} does not exist")
        component = self.components[component_name]
       
        if component_input_name not in component.inputs.keys():
            raise ValueError(f"Component {component_name} does not have input wire {component_input_name}")

        # Create a new input wire if one doesn't exist in the parent circuit.
        if input_name not in self.inputs:
            self.inputs[input_name] = Wire()
        new_wire = self.inputs[input_name]

        # Get the old wire from the component. This is the one that needs to be replaced.
        old_wire = component.inputs[component_input_name]
        component.inputs[component_input_name] = new_wire

        # Propagate the new wiring into any subcomponents recursively
        self._propagate_wire_update(old_wire, new_wire, component)

    def _propagate_wire_update(self, old_wire, new_wire, component):
        """
        Recursively update any input wire in subcomponents of 'component' that
        matches the old_wire's unique id.
        """
        for subcomp in component.components.values():
            # Update inputs in subcomponent.
            for key, wire in subcomp.inputs.items():
                if wire.id == old_wire.id:
                    subcomp.inputs[key] = new_wire
            # Also update outputs if needed.
            for key, wire in subcomp.outputs.items():
                if wire.id == old_wire.id:
                    subcomp.outputs[key] = new_wire
            # Recurse further.
            self._propagate_wire_update(old_wire, new_wire, subcomp)

    def add_output(self, output_name, component_name, component_output_name):
        if self.components[component_name] is None:
            raise ValueError(f"Component {component_name} does not exist")
        component = self.components[component_name]
       
        if component_output_name not in component.outputs:
            raise ValueError(f"Component {component_name} does not have output wire {component_output_name}")

        # Create (or reuse) a wire in the parent.
        if output_name not in self.outputs:
            self.outputs[output_name] = Wire()
        new_wire = self.outputs[output_name]

        # Get the old wire from the component and perform replacement.
        old_wire = component.outputs[component_output_name]
        component.outputs[component_output_name] = new_wire

        # Propagate the output wiring to subcomponents recursively.
        self._propagate_wire_update(old_wire, new_wire, component)

    def add_wire(self, name_a, out_a, name_b, in_b):
        if self.components[name_a] is None:
            raise ValueError(f"Component {name_a} does not exist")
        a = self.components[name_a]
       
        if self.components[name_b] is None:
            raise ValueError(f"Component {name_b} does not exist")
        b = self.components[name_b]

        if a.outputs[out_a] is None:
            raise ValueError(f"Component {name_a} does not have output wire {out_a}")
        
        if b.inputs[in_b] is None:
            raise ValueError(f"Component {name_b} does not have input wire {in_b}")
        
        # TODO adapt comment
        old_wire = b.inputs[in_b]
        b.inputs[in_b] = a.outputs[out_a]

        self._propagate_wire_update(old_wire, a.outputs[out_a], b)

    def validate(self):
        # TODO : Tous les in sont câblés, tous les outs sont câblés, tous les composants sont câblés (?)
        assert(True)

    def reset(self):
        for wire in self.inputs.values():
            wire.state = None

        for wire in self.outputs.values():
            wire.state = None

        for component in self.components.values():
            component.reset()

        self.miss = 0

    def can_simulate(self):
        return all(wire.state != None for wire in self.inputs.values())

    def was_simulated(self):
        return all(wire.state != None for wire in self.outputs.values())

    def simulate(self):
        if not self.can_simulate() or self.was_simulated():
            return False

        if self.identifier == 0:
            inputs = list(self.inputs.values())
            a = inputs[0]
            b = inputs[1]
            out = list(self.outputs.values())[0]
            out.state = not(a.state and b.state)
            return True
        
        n_evaluated = 0
        while True:
            previous_n_evaluated = n_evaluated
            for component in self.components.values():
                if component.simulate():
                    n_evaluated += 1
                else:
                    self.miss += 1

            if n_evaluated == previous_n_evaluated:
                break

        return self.was_simulated()    
            

    def __repr__(self, indent=0):
        indent_str = ' ' * indent
        inputs_str = ', '.join(f'{k}: {repr(v)}' for k, v in self.inputs.items())
        outputs_str = ', '.join(f'{k}: {repr(v)}' for k, v in self.outputs.items())
        components_str = ',\n'.join(f'\n{indent_str}  {k}:\n  {v.__repr__(indent + 4)}' for k, v in self.components.items())
        return (f'{indent_str}Circuit(id={self.identifier},\n'
                f'{indent_str}  inputs=OrderedDict({inputs_str}),\n'
                f'{indent_str}  outputs=OrderedDict({outputs_str}),\n'
                f'{indent_str}  components=OrderedDict({components_str})\n'
                f'{indent_str})')