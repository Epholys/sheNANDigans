#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "operation.h"

void init_operation(Circuit *op)
{
    memset(op, 0, sizeof *op);
}