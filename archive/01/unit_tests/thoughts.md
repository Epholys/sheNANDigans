# Ideas for testing

## Want


Assertions:
    - debug-time assertion from regular code is used as test-like assertion

Minimal friction:
    - Define in a single line test fixtures. Automatically add unit tests to this fixture. Min friction to add fixtures to global test main fct.

UX:
    - if verbose: see all tests with ok. / KO!
    - summary at the end: #ok. #KO! which & why KO!

## How 

- use a macro if/ifdef/define chain with N_DEBUG and a env var for implementing a single 'assert()' function
- how to transmit data from  test fixtures to assertion and back ?
    - ptr to int return code?
    - char* for message errors? i don't want to have a combo puts+exit for tests
        - where to put msg err ? global char* mgs\[VAR\]?
    - how to have a commun assert fn that have the minimalism of exit and the features necessary for tests
