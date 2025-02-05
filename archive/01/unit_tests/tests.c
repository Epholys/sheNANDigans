#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "test_framework.h"
#include "ring.h"

UNIT_TEST(test_ring_pop)
{
    Ring ring;
    ring.idx_begin = 0;
    ring.size = 8;
    ring.capacity = 15;
    Module test[5] = {0};
    ring.modules = test;
    pop_module(&ring);
    // tassert(false, "fail");
    tassert(true, "successA");
    tassert(true, "successB");
}
END_TEST

int main()
{
    test_ring_pop();
    run_tests();
}