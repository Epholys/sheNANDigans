from copy import deepcopy


class Wire:
    i = 0

    def __init__(self, state=None):
        self.state = state
        self.id = Wire.i
        Wire.i += 1

    def __repr__(self):
        return f"Wire(id={self.id}, state={self.state})"
    
    def __str__(self):
        bin = "0" if self.state == False else "1" if self.state == True else "X"
        return bin

class Circuit:
    def __init__(self, identifier, name=None, components=None):
        self.identifier = identifier
        self.name = name
        self.inputs = {}
        self.outputs = {}
        self.components = {}
        self.miss = 0

        if identifier == 0:
            self.name = "NAND"
            self.inputs["A"] = Wire()
            self.inputs["B"] = Wire()
            self.outputs["OUT"] = Wire()

    def add_component(self, name, component):
        self.components[name] = component

    def add_input(self, input_name, component_name, component_input_name):        
        if self.components[component_name] is None:
            raise ValueError(f"Component {component_name} does not exist")
        component = self.components[component_name]
       
        if component.inputs[component_input_name] is None:
            raise ValueError(f"Component {component_name} does not have input wire {component_input_name}")

        if input_name not in self.inputs:
            self.inputs[input_name] = Wire()

        component.inputs[component_input_name] = self.inputs[input_name]

    def add_output(self, output_name, component_name, component_output_name):
        if self.components[component_name] is None:
            raise ValueError(f"Component {component_name} does not exist")
        component = self.components[component_name]
       
        if component_output_name not in component.outputs:
            raise ValueError(f"Component {component_name} does not have output wire {component_output_name}")

        self.outputs[output_name] = component.outputs[component_output_name]

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
        
        a.outputs[out_a] = b.inputs[in_b]

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
            self.miss += 1
            return False

        if self.identifier == 0:
            if self.inputs["A"].state == True and self.inputs["B"].state == True:
                self.outputs["OUT"].state = False
            else:
                self.outputs["OUT"].state = True
            return True
        
        n_evaluated = 0
        while True:
            previous_n_evaluated = n_evaluated
            
            for component in self.components.values():
                if component.simulate():
                    n_evaluated += 1

            if n_evaluated == previous_n_evaluated:
                break

        return self.was_simulated()    
            

    def __repr__(self):
        return f"Circuit(id={self.identifier}, inputs={self.inputs}, outputs={self.outputs}, components={self.components})"

# Example usage
if __name__ == "__main__":
    print("--- NOT ---")

    not_gate = Circuit(identifier=1, name="NOT")
    not_gate.add_component("NAND", Circuit(identifier=0))
    not_gate.add_input("IN", "NAND", "A")
    not_gate.add_input("IN", "NAND", "B")
    not_gate.add_output("OUT", "NAND", "OUT")

    print(not_gate)

    not_gate.inputs["IN"].state = True

    print(f"inputs: {not_gate.inputs}")
    print(f"Simulation success: {not_gate.simulate()}")
    print(f"outputs: {not_gate.outputs}")

    not_gate.inputs["IN"].state = True

    print(f"inputs: {not_gate.inputs}")
    print(f"Simulation success: {not_gate.simulate()}")
    print(f"outputs: {not_gate.outputs}")

    print("--- AND ---")

    and_gate = Circuit(identifier=2, name="AND")
    and_gate.add_component("NAND", Circuit(identifier=0))
    and_gate.add_component("NOT", deepcopy(not_gate))
    and_gate.add_input("A", "NAND", "A")
    and_gate.add_input("B", "NAND", "B")
    and_gate.add_output("OUT", "NOT", "OUT")
    and_gate.add_wire("NAND", "OUT", "NOT", "IN")

    print(and_gate)

    and_gate.reset()
    and_gate.inputs["A"].state = False
    and_gate.inputs["B"].state = False
    print("0 AND 0")
    print(f"inputs: {and_gate.inputs}")
    print(f"Simulation success: {and_gate.simulate()}")
    print(f"outputs: {and_gate.outputs}")

    and_gate.reset()
    and_gate.inputs["A"].state = False
    and_gate.inputs["B"].state = True
    print("0 AND 1")
    print(f"inputs: {and_gate.inputs}")
    print(f"Simulation success: {and_gate.simulate()}")
    print(f"outputs: {and_gate.outputs}")

    and_gate.reset()
    and_gate.inputs["A"].state = True
    and_gate.inputs["B"].state = False
    print("1 AND 0")
    print(f"inputs: {and_gate.inputs}")
    print(f"Simulation success: {and_gate.simulate()}")
    print(f"outputs: {and_gate.outputs}")

    and_gate.reset()
    and_gate.inputs["A"].state = True
    and_gate.inputs["B"].state = True
    print("1 AND 1")
    print(f"inputs: {and_gate.inputs}")
    print(f"Simulation success: {and_gate.simulate()}")
    print(f"outputs: {and_gate.outputs}")
    print(f"miss: {and_gate.miss}")

    print("--- OR ---")

    or_gate = Circuit(identifier=3, name="OR")
    or_gate.add_component("NAND_A", Circuit(identifier=0))
    or_gate.add_component("NAND_B", Circuit(identifier=0))
    or_gate.add_component("NAND_OUT", Circuit(identifier=0))

    or_gate.add_input("A", "NAND_A", "A")
    or_gate.add_input("A", "NAND_A", "B")
    or_gate.add_input("B", "NAND_B", "A")
    or_gate.add_input("B", "NAND_B", "B")

    or_gate.add_output("OUT", "NAND_OUT", "OUT")

    or_gate.add_wire("NAND_A", "OUT", "NAND_OUT", "A")
    or_gate.add_wire("NAND_B", "OUT", "NAND_OUT", "B")

    or_gate.reset()
    or_gate.inputs["A"].state = False
    or_gate.inputs["B"].state = False
    print("0 AND 0")
    print(f"inputs: {or_gate.inputs}")
    print(f"Simulation success: {or_gate.simulate()}")
    print(f"outputs: {or_gate.outputs}")

    or_gate.reset()
    or_gate.inputs["A"].state = False
    or_gate.inputs["B"].state = True
    print("0 AND 1")
    print(f"inputs: {or_gate.inputs}")
    print(f"Simulation success: {or_gate.simulate()}")
    print(f"outputs: {or_gate.outputs}")

    or_gate.reset()
    or_gate.inputs["A"].state = True
    or_gate.inputs["B"].state = False
    print("1 AND 0")
    print(f"inputs: {or_gate.inputs}")
    print(f"Simulation success: {or_gate.simulate()}")
    print(f"outputs: {or_gate.outputs}")

    or_gate.reset()
    or_gate.inputs["A"].state = True
    or_gate.inputs["B"].state = True
    print("1 AND 1")
    for name, wire in or_gate.inputs.items():
        print(f"{name} {wire}")
    print(f"Simulation success: {or_gate.simulate()}")
    for name, wire in or_gate.outputs.items():
        print(f"{name} {wire}")
    print(f"miss: {or_gate.miss}")

    # TODO Continuer jusqu'à full 4-bit adder
    # TODO Ajouter BDD pour stocker les circuits
    # TODO Ajouter tableau de vérité pour chaque circuit
    # TODO Ajouter Graphviz
