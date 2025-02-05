#ifndef ASSERT_H
#define ASSERT_H

#include <stdbool.h>
#include <assert.h>

void tassert(bool success, char *condition, char *message, char *filename, char const *func, int line);

#ifndef TEST
#define ASSERT(CONDITION, MESSAGE, RETURN_VALUE) assert(CONDITION);
#else
#define TASSERT(CONDITION, MESSAGE) tassert(CONDITION, #CONDITION, MESSAGE, __FILE__, __func__, __LINE__);
#define ASSERT_V(CONDITION, MESSAGE) \
    TASSERT(CONDITION, MESSAGE);     \
    if (!(CONDITION))                \
    {                                \
        return;                      \
    }
#define ASSERT(CONDITION, MESSAGE, RETURN_VALUE) \
    TASSERT(CONDITION, MESSAGE);                 \
    if (!(CONDITION))                            \
    {                                            \
        return RETURN_VALUE;                     \
    }
#endif

#endif // ASSERT_H