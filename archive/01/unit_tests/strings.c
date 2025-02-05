#include <stdio.h>
#include "strings.h"

void print_to_array(char *dest, int size, char *source) {
    snprintf(dest, size, "%s", source);
}