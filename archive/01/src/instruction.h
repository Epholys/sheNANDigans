#ifndef INSTRUCTION_H
#define INSTRUCTION_H

#include "data.h"

void build_and_push_instr(Circuit *op, int *args, int nArgs, int opIdx);
void push_instr(Circuit *op, Module isntr);
// Module *pop_instr(Circuit *op);

#endif