#ifndef TEST_FRAMEWORK_H
#define TEST_FRAMEWORK_H

#include <stdbool.h>

#define MESSAGE_LENGTH 128

typedef struct AssertResult
{
    bool success;
    char message[MESSAGE_LENGTH];
} AssertResult;

void tassert(bool condition, char *message);
void add_test(char *name);
void ensure_failure();
void run_tests();

typedef void (*test_fn)(void);

#define UNIT_TEST(NAME) \
    void NAME()    \
    {              \
        add_test(#NAME);
#define END_TEST }

#endif // TEST_FRAMEWORK_H