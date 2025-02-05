#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "ring.h"
#include "instruction.h"

void build_and_push_instr(Circuit *op, int *args, int nArgs, int opIdx)
{
    if (nArgs >= WIRE_SIZE)
    {
        puts("push_instr: too many args");
        exit(-1);
    }

    Module instr;
    memcpy(instr.wirings, args, sizeof(int) * nArgs);
    instr.id_circuit = opIdx;

    push_instr(op, instr);
}

void push_instr(Circuit *op, Module module)
{
    op->modules[op->n_modules] = module;
    op->n_modules++;
    if (op->n_modules >= MAX_OPS)
    {
        puts("push_instr: MAX_OPS too short");
        exit(-1);
    }
}

/*
Module *pop_instr(Circuit *op)
{
    Ring *q = &op->modules;

    if (q->size == 0)
    {
        puts("pop_instr: trying to pop empty queue");
        exit(-1);
    }
    if (q->idx_begin == q->idx_end)
    {
        puts("pop_instr: begin caught up to end, should not happen, size managment error");
        exit(1);
    }

    Module *instr = q->modules + q->idx_begin;

    q->size--;
    q->idx_begin++;
    if (q->idx_begin >= MAX_OPS)
    {
        q->idx_begin = 0;
    }

    return instr;
}
*/
