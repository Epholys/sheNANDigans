#ifndef RING_H
#define RING_H

#include "data.h"

typedef struct Ring
{
    int capacity;
    int size;
    int idx_begin;
    int idx_end;
    Module modules[MAX_OPS];
} Ring;

void assert_valid_circuit(Circuit circuit);
Ring init_ring(Circuit circuit);
void push_module(Ring *ring, Module module);
Module pop_module(Ring *ring);

#endif