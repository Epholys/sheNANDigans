class Wire:
    def __init__(self, name, state=None):
        self.name = name
        self.state = state

    def __repr__(self):
        return f"Wire(name={self.name}, state={self.state}, connected_to={self.connected_to.name if self.connected_to else None})"

class Circuit:
    def __init__(self, identifier, name, components=None):
        self.identifier = identifier # TO KEEP : id global indiquant le circuit
        self.name = name # TO KEEP : nom du composant dans un circuit plus grand
         # A ADAPTER : on doit avoir pour une liste de in et out
         # + une liste de fils : le fil est créé à la volée et contient juste un état : il est placé dans in circuit et in composant
         # idem pour out
         # simulation : in propagé
         # puis simulation
         # puis out propagé 
        self.input_wires = {}
        self.output_wires = {}
        self.components = {}
        self.evaluated = False

        if identifier == 0:
            self.add_input_wire("A")
            self.add_input_wire("B")
            self.add_output_wire("OUT")

    def add_input_wire(self, name, state=None):
        self.input_wires[name] = state

    def add_output_wire(self, name, state=None):
        self.output_wires[name] = state

    def add_component(self, name, component):
        self.components[name] = component

    def connect_input(self, wire_name, component, component_input_name):
        print(wire_name, component, component_input_name)
        
        for wire in self.input_wires.keys():
            print(wire, wire_name)
            if wire.name == wire_name:
                if component.input_wires[component_input_name] is None:
                    component.input_wires[component_input_name] = Wire(component_input_name)
                wire.connect(component.input_wires[component_input_name])
                print(wire, component.input_wires, wire.connected_to)
                return
        else:
            raise ValueError(f"Input wire {wire_name} does not exist")

    def connect_output(self, wire_name, component, component_output_name):
        for wire in self.output_wires.keys():
            if wire.name == wire_name:
                self.output_wires[wire_name].connect(component.output_wires[component_output_name])
                return
        else:
            raise ValueError(f"Output wire {wire_name} does not exist")

    def get_input_count(self):
        return len(self.input_wires)
    
    def get_output_count(self):
        return len(self.output_wires)
    
    def reset(self):
        self.evaluated = False
        for component in self.components:
            component.reset()

    def simulate(self):
        if self.evaluated:
            return
        
        if self.identifier == 0:
            if self.input_wires["A"].state == None or self.input_wires["B"].state == None:
                return
            if self.input_wires["A"].state == True and self.input_wires["B"].state == True:
                self.output_wires["OUT"].state = False
            else:
                self.output_wires["OUT"].state = True
            self.evaluated = True
            return

        # Set component input wires based on circuit input wires
        for wire in self.input_wires.items():
            if wire.connected_to:
                wire.connected_to.state = wire.state

        
        converged = False
        evaluated_components = {}
        n_evaluated_components = 0
        while not converged:
            for component in self.components:
                component.simulate()

            converged = True
            for component in self.components:
                if component.evaluated:
                    evaluated_components.add(component)
            
            if len(evaluated_components) == n_evaluated_components:
                converged = True
            else:
                n_evaluated_components = len(evaluated_components)

        # Check if all output wires are set
        for wire in self.output_wires.items():
            if wire.connected_to:
                wire.state = wire.connected_to.state
            if wire.state is None:
                raise RuntimeError(f"Output wire {wire_name} is not set")
            

    def __repr__(self):
        return f"Circuit(id={self.identifier}, inputs={self.input_wires}, outputs={self.output_wires}, components={self.components})"

# Example usage
if __name__ == "__main__":
    circuit = Circuit(identifier=1, name="DUMMY")
    circuit.add_input_wire(Wire("A"))
    circuit.add_input_wire(Wire("B"))
    circuit.add_output_wire(Wire("OUT"))
    print(circuit)

    circuit.add_component("COMPONENT", Circuit(identifier=0, name="NAND"))

    print(circuit)

    circuit.connect_input("A", circuit.components["COMPONENT"], "A")
    circuit.connect_input("B", circuit.components["COMPONENT"], "B")
    
    print(circuit)

    circuit.connect_output("OUT", circuit.components["COMPONENT"], "OUT")

    print(circuit)
# 