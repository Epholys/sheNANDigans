#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include "test_framework.h"
#include "macro.h"
#include "strings.h"

#define N_TEST 32
#define N_ASSERT 16
#define NAME_LENGTH 64

typedef struct Test
{
    char name[NAME_LENGTH];
    bool success;
    int results_size;
    AssertResult results[N_ASSERT];
} Test;

static struct TestArray
{
    int size;
    Test tests[N_TEST];
} all_tests = {0};

Test *current_test() {
    return &all_tests.tests[all_tests.size - 1];
}

void tassert(bool condition, char *message) {
    AssertResult result = {
        .success = condition,
        .message = {0}
    };
    print_to_array(result.message, ARRAY_LENGTH(result.message), message);
    push_result(result);
}

void push_result(AssertResult result)
{
    Test *test = current_test();
    
    test->success &= result.success;
    test->results[test->results_size] = result;
    test->results_size++;

    assert(test->results_size < ARRAY_LENGTH(test->results));
}

void add_test(char *name)
{
    assert(name != NULL);

    Test new_test = {
        .name = {0},
        .success = true,
        .results_size = 0,
        .results = {0}
        };
    print_to_array(new_test.name, ARRAY_LENGTH(new_test.name), name);

    all_tests.tests[all_tests.size] = new_test;
    all_tests.size++;
   
    assert(all_tests.size < ARRAY_LENGTH(all_tests.tests));
}

void run_tests()
{
    char *ok = "ok.";
    char *KO = "KO!";
    for (int i = 0; i < all_tests.size; i++)
    {
        Test test = all_tests.tests[i];
        printf("%s ", test.name);
        if (!test.success)
        {
            puts(KO);
            for (int j = 0; j < test.results_size; j++)
            {
                AssertResult result = test.results[j];
                char *success = result.success ? ok : KO;
                printf("\t%s %s\n", result.message, success);
            }
        }
        else
        {
            puts(ok);
        }
    }
}