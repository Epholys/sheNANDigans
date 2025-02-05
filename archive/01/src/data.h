#ifndef DATA_H
#define DATA_H

#define STACK_DEPTH 8
#define WIRE_SIZE 32 // TODO 256
#define OPS_COUNT 32
#define MAX_OPS 32
#define IN_BUF_SIZE 1024

// TODO Use int8_t
typedef unsigned char byte;

typedef struct Module
{
    int id_circuit;
    int wirings[WIRE_SIZE];
} Module;

typedef struct Circuit
{
    int n_inputs;
    int n_outputs;
    int n_modules;
    Module modules[MAX_OPS]; 
} Circuit;

typedef enum WireState
{
    UNDEFINED = 0,
    OFF,
    ON,
} WireState;

extern WireState STACK[STACK_DEPTH][WIRE_SIZE];
extern Circuit CIRCUITS[OPS_COUNT];

#endif