#include <assert.h>
#include <stddef.h>
#include <string.h>
#include <limits.h>
#include <stdbool.h>
#include "ring.h"
#include "macro.h"

void assert_valid_circuit(Circuit circuit)
{
    assert(circuit.n_inputs > 0);
    assert(circuit.n_outputs > 0);
    assert(circuit.n_modules > 0);
    long unsigned int length = ARRAY_LENGTH(circuit.modules);
    assert(length < INT_MAX);
    assert(circuit.n_modules < (int)length);
}

void assert_valid_ring(Ring ring)
{
    assert(ring.capacity > 0);
    assert(ring.size >= 0);
    assert(ring.size <= ring.capacity);
    assert(ring.idx_begin >= 0);
    assert(ring.idx_begin < ring.capacity);
    assert(ring.idx_end >= 0);
    assert(ring.idx_end < ring.capacity);
}

Ring init_ring(Circuit circuit)
{
    assert_valid_circuit(circuit);

    Ring ring = {
        .capacity = -1,
        .size = circuit.n_modules,
        .idx_begin = 0,
        .idx_end = circuit.n_modules,
        .modules = {0}};
    ring.capacity = ARRAY_LENGTH(ring.modules);
    memcpy(ring.modules, circuit.modules, sizeof(circuit.modules));

    assert_valid_ring(ring);
    return ring;
}

Module pop_module(Ring *ring)
{
    assert(ring != NULL);
    assert_valid_ring(*ring);
    assert(ring->size > 0);

    Module module = ring->modules[ring->idx_begin];
    ring->idx_begin = (ring->idx_begin + 1) % ring->capacity;
    ring->size--;

    assert_valid_ring(*ring);
    return module;
}

void push_module(Ring *ring, Module module)
{
    assert(ring != NULL);
    assert_valid_ring(*ring);
    assert(ring->size < ring->capacity);

    ring->modules[ring->idx_end] = module;
    ring->idx_end = (ring->idx_end + 1) % ring->capacity;
    ring->size++;

    assert_valid_ring(*ring);
}
