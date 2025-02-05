#include "data.h"
#include "ring.h"

// <<<circuit_negative_n_in>>>
void circuit_negative_n_in()
{
    Circuit circuit =
        {.n_inputs = -1,
         .n_outputs = 2,
         .n_modules = 1,
         .modules = {0}};
    assert_valid_circuit(circuit);
}

// <<<circuit_negative_n_out>>>
void circuit_negative_n_out()
{
    Circuit circuit =
        {.n_inputs = 2,
         .n_outputs = -1,
         .n_modules = 1,
         .modules = {0}};
    assert_valid_circuit(circuit);
}

// <<<circuit_negative_n_module>>>
void circuit_negative_n_module()
{
    Circuit circuit =
        {.n_inputs = 2,
         .n_outputs = 2,
         .n_modules = -1,
         .modules = {0}};
    assert_valid_circuit(circuit);
}

// <<<circuit_too_big_n_module>>>
void circuit_too_big_n_module()
{
    Circuit circuit =
        {.n_inputs = 2,
         .n_outputs = 2,
         .n_modules = MAX_OPS,
         .modules = {0}};
    assert_valid_circuit(circuit);
}
