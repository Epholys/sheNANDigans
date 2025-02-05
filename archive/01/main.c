#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include <stdbool.h>

#include "data.h"
#include "interpreter.h"
#include "instruction.h"
#include "operation.h"
#include "ring.h"



static int nand_simulated_count = 0;
static int retry_count = 0;

void print_stack();
char wireToChar(WireState w);
void testing_bed_op();
bool simulate_nand(int lvl)
{
    WireState nand = UNDEFINED;
    WireState first = STACK[lvl][0];
    WireState second = STACK[lvl][1];
    if (first != UNDEFINED && second != UNDEFINED)
    {
        nand = (first == ON && second == ON) ? OFF : ON;
    }
    STACK[lvl][2] = nand;
    nand_simulated_count++;
    return nand != UNDEFINED;
}

bool simulate_circuit(int circuit_id, int stack_depth)
{
    assert(stack_depth >= 0);
    assert(stack_depth < STACK_DEPTH - 1);
    assert(circuit_id >= 0);

    Circuit circuit = CIRCUITS[circuit_id];
    Ring ring = init_ring(circuit);

    int initial_ring_size = ring.size;
    int modules_remaining = ring.size;
    while (true)
    {
        Module module = pop_module(&ring);
        int sub_circuit_id = module.id_circuit;
        int n_inputs = CIRCUITS[sub_circuit_id].n_inputs;
        int n_outputs = CIRCUITS[sub_circuit_id].n_outputs;
        int *wirings = module.wirings;

        // Push new level of memory stack with the input wires.
        stack_depth++;
        for (int in = 0; in < n_inputs; ++in)
        {
            STACK[stack_depth][in] = STACK[stack_depth - 1][wirings[in]];
        }

        // Simulate the module's circuit.
        bool success = (sub_circuit_id == 0) ? simulate_nand(stack_depth) : simulate_circuit(sub_circuit_id, stack_depth);

        // The simulation failed, delay it to later.
        if (!success)
        {
            push_module(&ring, module);
        }

        // Pop the outputs of the simulation to the previous level of memory stack.
        for (int out = n_inputs; out < n_inputs + n_outputs; out++)
        {
            STACK[stack_depth - 1][wirings[out]] = STACK[stack_depth][out];
        }
        stack_depth--;

        modules_remaining--;
        // If we tried to do all operations:
        if (modules_remaining == 0)
        {
            // No module simulations were successful, partial result.
            if (ring.size == initial_ring_size)
            {
                return false;
            }
            // All module simulations successful!
            else if (ring.size == 0)
            {
                return true;
            }
            // Some module simulations were delayed, try again with the failed modules left on the ring.
            else if (ring.size > 0 && ring.size < initial_ring_size)
            {
                modules_remaining = ring.size;
                initial_ring_size = ring.size;
                retry_count++;
            }
            else
            {
                bool missing_case_on_simulation_loop = false;
                assert(missing_case_on_simulation_loop);
            }
        }
    }
}

void check4bitsAdder();

void pprintOp(int idx)
{
    Circuit dbg = CIRCUITS[idx];
    printf("number of input of op: %d\n", dbg.n_inputs);
    printf("number of output of op: %d\n", dbg.n_outputs);
    printf("instructions of op:\n");
    Ring queue = init_ring(dbg);
    int n = 0;
    for (int i = queue.idx_begin; i != queue.idx_end;)
    {
        printf("Instr #%d, at idx %d\n", n, i);
        Module instr = queue.modules[i];
        Circuit instrOp = CIRCUITS[instr.id_circuit];

        printf("Args: ");
        for (int j = 0; j < instrOp.n_inputs + instrOp.n_outputs; j++)
        {
            printf("%d ", instr.wirings[j]);
        }
        putc('\n', stdout);

        printf("Op: %d\n", instr.id_circuit);

        n++;
        i++;
        if (i == MAX_OPS)
        {
            i = 0;
        }
    }
    puts("\n\n");
}
char wireToChar(WireState w)
{
    switch (w)
    {
    case UNDEFINED:
        return '?';
    case OFF:
        return '0';
    case ON:
        return '1';
    default:
        bool unknown_wire_state = false;
        assert(unknown_wire_state);
    }
}
void print_stack()
{
    return;

    for (int i = 0; i < STACK_DEPTH; i++)
    {
        for (int j = 0; j < WIRE_SIZE; j++)
        {
            putc(wireToChar(STACK[i][j]), stdout);
        }
        putc('\n', stdout);
    }
    puts("--------");
}
int main()
{
    Circuit nand = {
        .n_inputs = 2,
        .n_outputs = 1,
        .n_modules = 1,
        .modules = {0}};
    CIRCUITS[0] = nand;

    byte not [6] = {0b11000001, 0b10000000, 0b00000000, 0b00000000, 0b00000001, 0b11000001};
    interpret(not, 6);

/*
    Xtrem comprssion à partir de Claude :
    0   - Circuit ID   a bits (Définition)
    1   - Input Count  b bits
    2   - Output Count c bits
    3   - Gate Count   d bits
    4_0 - Circuit ID   a bits   (Application)                        |
    4_1 - Source index d+1 bits (avec câbles input) | × 2^id_b + 2^id_c  |
    4_2 - Source-Output Index ID.OutputCount bits   |              | × 2^d
    ...                                                            |
    d_2                                                            |
    idem × c
*/

    /*
    Pour 16 circuits: 5 bits
    Pour 16 input count : 5 bits
    Pour 16 output count : 5 bits
    Pour 16 gate count : 5 bits
    and
    00010 id = 5
    00010 2 in
    00001 1 out
    00001 1 gate
    00000 nand : 2 in = 1 bit 1 out = 1 bit
    0-0 : input 1er <- 1 gate donc in donc diminuer à 1
    0-1 : input 2e
    0   : out 1er <- diminuer à 0 car nand out = 1
    end gates
    5 + 5 + 5 + 5 + 5 + 2 + 2 + 1 =10 + 10 + 10  = 30  (27)
    */

    byte and[9] = { // 9 × 8 = 72 bits
        0b11000010, // DEF 2
        0b10000000, // APP 0
        0b00000000, // LIT 0
        0b00000001, // LIT 1
        0b00000011, // LIT 3
        0b10000001, // APP 1
        0b00000011, // LIT 3
        0b00000010, // LIT 2
        0b11000010  // DEF 2
    };
    interpret(and, 9);

    byte or [14] = {
        0b11000011, // DEF3
        0b10000000, // APP 0
        0b00000000, // LIT 0
        0b00000000, // LIT 0
        0b00000011, // LIT 3
        0b10000000, // APP 0
        0b00000001, // LIT 1
        0b00000001, // LIT 1
        0b00000100, // LIT 4
        0b10000000, // APP 0
        0b00000011, // LIT 3
        0b00000100, // LIT 4
        0b00000010, // LIT 2
        0b11000011, // DEF3

    };
    interpret(or, 14);

    byte nor[9] = {
        0b11000100, // DEF4
        0b10000011, // APP 3
        0b00000000, // LIT 0
        0b00000001, // LIT 1
        0b00000011, // LIT 3
        0b10000001, // APP 1
        0b00000011, // LIT 3
        0b00000010, // LIT 2
        0b11000100, // DEF3
    };
    interpret(nor, 9);

    byte xor [18] = {
        0b11000101, // DEF5
        0b10000000, // APP 0
        0b00000000, // LIT 0
        0b00000001, // LIT 1
        0b00000011, // LIT 3
        0b10000000, // APP 0
        0b00000000, // LIT 0
        0b00000011, // LIT 3
        0b00000100, // LIT 4
        0b10000000, // APP 0
        0b00000001, // LIT 1
        0b00000011, // LIT 3
        0b00000101, // LIT 5
        0b10000000, // APP 0
        0b00000100, // LIT 4
        0b00000101, // LIT 5
        0b00000010, // LIT 2
        0b11000101, // DEF5
    };
    interpret(xor, 18);

    byte halfAdd[10] = {
        0b11000110, // DEF6
        0b10000101, // APP 5
        0b00000000, // LIT 0
        0b00000001, // LIT 1
        0b00000011, // LIT 3
        0b10000010, // APP 2
        0b00000000, // LIT 0
        0b00000001, // LIT 1
        0b00000010, // LIT 2
        0b11000110, // DEF6
    };
    interpret(halfAdd, 10);

    byte fullAdd[22] = { // 22 * 8 = 176 bits
        0b11000111, // DEF7
        0b10000101, // APP 5
        0b00000000, // LIT 0
        0b00000001, // LIT 1
        0b00000101, // LIT 5
        0b10000101, // APP 5
        0b00000101, // LIT 5
        0b00000010, // LIT 2
        0b00000100, // LIT 4
        0b10000010, // APP 2
        0b00000101, // LIT 5
        0b00000010, // LIT 2
        0b00000110, // LIT 6
        0b10000010, // APP 2
        0b00000000, // LIT 0
        0b00000001, // LIT 1
        0b00000111, // LIT 7
        0b10000011, // APP 3
        0b00000110, // LIT 6
        0b00000111, // LIT 7
        0b00000011, // LIT 3
        0b11000111, // DEF7
    };
    interpret(fullAdd, 22);

    byte fourBitAdd[26] = {
        0b11001000, // DEF8

        0b10000111, // APP 7
        0b00000011, // LIT 3
        0b00000111, // LIT 7
        0b00001000, // LIT 8
        0b00001110, // LIT e
        0b00001101, // LIT d

        0b10000111, // APP 7
        0b00000010, // LIT 2
        0b00000110, // LIT 6
        0b00001110, // LIT e
        0b00001111, // LIT f
        0b00001100, // LIT c

        // UNOPTIMIZED
        // 0b10000111, // APP 7
        // 0b00000000, // LIT 0
        // 0b00000100, // LIT 4
        // 0b00010000, // LIT 10
        // 0b00001001, // LIT 9
        // 0b00001010, // LIT a
        // END UNOPTIMIZED

        0b10000111, // APP 7
        0b00000001, // LIT 1
        0b00000101, // LIT 5
        0b00001111, // LIT f
        0b00010000, // LIT 10
        0b00001011, // LIT b

        0b10000111, // APP 7
        0b00000000, // LIT 0
        0b00000100, // LIT 4
        0b00010000, // LIT 10
        0b00001001, // LIT 9
        0b00001010, // LIT a

        0b11001000, // DEF8
    };
    interpret(fourBitAdd, 26);

    testing_bed_op();

    printf("Number of retries: %d\n", retry_count);
    printf("NAND simulation realized: %d", nand_simulated_count);
}

void testing_bed_op()
{

    STACK[0][0] = OFF;
    STACK[0][1] = ON;

    // Apply OP
    int opIdx = 4; // 4 = NOR
    simulate_circuit(opIdx, 0);
    Circuit op = CIRCUITS[opIdx];

    puts("*** RESULT : ***");
    puts("INPUT: ");
    for (int in = 0; in < op.n_inputs; ++in)
    {
        putc(wireToChar(STACK[0][in]), stdout);
    }
    puts("\nOUTPUT: ");
    for (int out = op.n_inputs; out < op.n_inputs + op.n_outputs; ++out)
    {
        putc(wireToChar(STACK[0][out]), stdout);
    }
    putc('\n', stdout);

    // Set STACK
    /*
    STACK[0][0] = ON;  // A = 1
    STACK[0][1] = OFF; // A = 10
    STACK[0][2] = ON;  // A = 101
    STACK[0][3] = OFF; // A = 1010 = 10
    STACK[0][4] = OFF; // B = 0
    STACK[0][5] = OFF; // B = 00
    STACK[0][6] = ON;  // B = 001
    STACK[0][7] = ON;  // B = 0011 = 3
    STACK[0][8] = OFF; // C0 = 0
    // RES = A + B + C = 13 = 01101
    */

    check4bitsAdder();
}

WireState intToWire(int x)
{
    return (x == 0 ? OFF : (x == 1 ? ON : UNDEFINED));
}
int wireToInt(WireState w)
{
    return (w == OFF ? 0 : (w == ON ? 1 : -1));
}

void check4bitsAdder()
{
    for (int a = 0; a < 16; a++)
    {
        for (int b = 0; b < 16; b++)
        {
            for (int c = 0; c < 2; c++)
            {
                memset(STACK[0], UNDEFINED, sizeof(WireState) * WIRE_SIZE);

                WireState a3 = intToWire((a >> 3) & 1);
                WireState a2 = intToWire((a >> 2) & 1);
                WireState a1 = intToWire((a >> 1) & 1);
                WireState a0 = intToWire((a >> 0) & 1);
                WireState b3 = intToWire((b >> 3) & 1);
                WireState b2 = intToWire((b >> 2) & 1);
                WireState b1 = intToWire((b >> 1) & 1);
                WireState b0 = intToWire((b >> 0) & 1);
                WireState c0 = intToWire(c);
                STACK[0][0] = a3;
                STACK[0][1] = a2;
                STACK[0][2] = a1;
                STACK[0][3] = a0;
                STACK[0][4] = b3;
                STACK[0][5] = b2;
                STACK[0][6] = b1;
                STACK[0][7] = b0;
                STACK[0][8] = c0;

                simulate_circuit(8, 0);

                int c1 = wireToInt(STACK[0][9]);
                int s3 = wireToInt(STACK[0][0xa]);
                int s2 = wireToInt(STACK[0][0xb]);
                int s1 = wireToInt(STACK[0][0xc]);
                int s0 = wireToInt(STACK[0][0xd]);

                int s = (c1 << 4) + (s3 << 3) + (s2 << 2) + (s1 << 1) + s0;
                int truth = a + b + c;
                if (s != truth)
                {
                    printf("ERROR!!! %d + %d (+%d) = %d INSTEAD OF %d\n", a, b, c, s, truth);
                    printf("s3 is %d instead of %d\n\n", s3, (truth >> 3) & 1);
                }
            }
        }
    }
}