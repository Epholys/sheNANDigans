# SheNANDigans

## What's this project?

This is a toy playground to explore the beauty of the NAND gate.

It started as a way to experiment creating the smallest encoding possible of logical circuits, but it took a life of its own, with nested definitions of circuits, visualization, simulation, and more to come!

## What are NAND anyways?

The NAND is a logic gate: it has two inputs that can be true or false, and it produces an output which is false only is both the inputs are true. (Its name come from that it's the complement of the AND gate: NOT + AND.)

This simple rule has an awesome property: from it, every possible logic gate can be realized, without any other component. This is what's called [functional completeness](https://en.wikipedia.org/wiki/Functional_completeness). It's possible to create all other "basic" gates (NOT, AND, OR, XOR, etc), and a bit higher up multiplexer or circuit that can perform additions (adder)... And that can goes on and on until creating the logic core of a CPU! [nand2tetris](https://www.nand2tetris.org/) is a course that takes this simple idea and go all the way up to CPU and cross the boundary into software. I can't recommend it enough!

## What does this pile of python files do?

Well, there's not really (for now!) a single entrypoint, or even some kind of main script... But the core is here! Here's some features:

- Defining in python the logical circuits in an iterative way. For example, without any context, heres a half-adder that adds two bits:

```py
def build_half_adder():
    half_adder = Circuit("Half-Adder")

    half_adder.add_component("XOR", self.get_schematic_idx(5)) # Previously defined
    half_adder.add_component("AND", self.get_schematic_idx(2))

    half_adder.connect_input("A", "XOR", "A")
    half_adder.connect_input("B", "XOR", "B")
    half_adder.connect_input("A", "AND", "A")
    half_adder.connect_input("B", "AND", "B")

    half_adder.connect_output("CARRY", "AND", "OUT")
    half_adder.connect_output("SUM", "XOR", "OUT")

    return half_adder
```

A way to simulate them:

```py
half_adder = build_half_adder()
simulator = build_simulator(half_adder, OptimizationLevel.FAST) # Automatically optimize
result = simulator.simulate([True, False])
assert result == [False, True] # 1 + 0 = 01
```

And a way to encode and decode:

```py
builder = SchematicsBuilder()
builder.build_circuits()
schematics = builder.schematics

reference_encoding: List[int] = CircuitEncoder(schematics).encode()
round_trip_schematics = CircuitDecoder(reference_encoding).decode()
round_trip_encoding = CircuitEncoder(round_trip_schematics).encode()

assert reference_encoding == round_trip_encoding
```

*All basic logic gates, and adders until 8-bits can be encoded into __262__ bytes!* And that's before planned bit-packing.

And, last but not least, a way to visualize:

```py
graph = generate_graph(
    half_adder,
    GraphOptions(is_compact=True, is_aligned=True, bold_io=True)
)
save_graph(graph, f"half_adder", "svg")
```

## What's next?

I have a lots of ideas:

- Encode the circuits into the least amount of bits possibles
- Fast parallelized simulations
- Simple DSL to define circuits
- Automated optimization and search
- Defining simple fantasy or real chips

## What's this "archive" directory?

Digital hoarding is a serious illness, I can't delete the dark past...