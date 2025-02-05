#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include "interpreter.h"
#include "operation.h"
#include "instruction.h"

typedef struct interpreter_state
{
    Circuit new_op;
    int new_op_Idx;

    int applying_op_literalCount;
    int applying_op_inCount;
    int applying_op_OutCount;
    int applying_op_AppIdx;
    int applying_op_defining_args[WIRE_SIZE];

    int in[WIRE_SIZE];
    int med[WIRE_SIZE];
    int out[WIRE_SIZE];
} interpreter_state;

typedef struct buffer
{
    byte data[IN_BUF_SIZE];
    int processed;
    int data_length;
    byte *source;
    int source_length_left;
} buffer;

struct sm_state;
typedef void state_fn(struct sm_state *state);
typedef struct sm_state
{
    state_fn *next;
    interpreter_state state;
    buffer buffer;
    byte b;
} sm_state;

void init_interpreter_state(interpreter_state *state)
{
    memset(state, 0, sizeof *state);
}

void begin(sm_state *state);
void read_to_buffer(buffer *buf);
void interpret(byte *data, int size)
{
    sm_state sm_state;

    if (size >= IN_BUF_SIZE)
    {
        // puts("Tring to fill a too big buffer, abort");
        exit(-1);
    }
    sm_state.buffer.processed = 0;
    sm_state.buffer.data_length = 0;
    sm_state.buffer.source = data;
    sm_state.buffer.source_length_left = size;
    read_to_buffer(&sm_state.buffer);

    sm_state.next = begin;
    init_interpreter_state(&sm_state.state);

    while (sm_state.next != NULL)
    {
        sm_state.next(&sm_state);
    }
    return;
}

void read_to_buffer(buffer *buf)
{

    buf->processed = 0;
    int to_read = buf->source_length_left < IN_BUF_SIZE ? buf->source_length_left : IN_BUF_SIZE;
    buf->source_length_left -= to_read;
    buf->data_length = to_read;
    memcpy(buf->data, buf->source, to_read);
}

void manage_buffer(buffer *buf)
{
    if (buf->processed == buf->data_length)
    {
        read_to_buffer(buf);
    }
}

byte *read_byte(buffer *buf)
{
    manage_buffer(buf);
    if (buf->data_length == 0)
    {
        return NULL;
    }
    return buf->data + buf->processed++;
}
byte *peek_byte(buffer *buf)
{
    manage_buffer(buf);
    if (buf->data_length == 0)
    {
        return NULL;
    }
    return buf->data + buf->processed;
}

#define OPERATION_BIT 7
#define DEFINE_BIT 6
#define OPERATION_MASK 0b0011111

int isOpDefined(int idx)
{
    assert(idx >= 0 && idx < OPS_COUNT);
    Circuit op = CIRCUITS[idx];
    if (idx != 0 && (op.n_inputs == 0 || op.n_outputs == 0 || op.n_modules == 0))
    {
        return 0;
    }
    return 1;
}

int check_in_args(int *args, int nIn)
{
    if (nIn < 0 || nIn >= WIRE_SIZE - 1)
    {
        // Too many args
        return 0;
    }
    for (int i = 0; i < nIn; i++)
    {
        if (args[i] == 0)
        {
            // Input not consecutive at beginning
            return 0;
        }
    }
    return 1;
}

int check_out_args(int *args, int nOut, int nIn)
{
    if (nOut < 0 || nOut >= WIRE_SIZE - 1)
    {
        // Too many args
        return 0;
    }
    for (int i = nIn; i < nIn + nOut; i++)
    {
        if (args[i] == 0)
        {
            // Out not consecutive at beginning
            return 0;
        }
    }
    return 1;
}

int check_instr_count(int count)
{
    if (count < 0 || count >= MAX_OPS)
    {
        return 0;
    }
    return 1;
}

int add_op(interpreter_state *state)
{
    int inOk = check_in_args(state->in, state->new_op.n_inputs);
    int outOk = check_out_args(state->out, state->new_op.n_outputs, state->new_op.n_inputs);
    int instrOk = check_instr_count(state->new_op.n_modules);
    if (inOk == 0 || outOk == 0 || instrOk == 0)
    {
        return 0;
    }

    CIRCUITS[state->new_op_Idx] = state->new_op;
    return 1;
}

int is_operation_instr(byte b)
{
    return (b >> OPERATION_BIT) & 1;
}
int is_define_limit_instr(byte b)
{
    return (b >> DEFINE_BIT) & 1;
}

void start_define(sm_state *sm_state);
void define_op_next_iter(sm_state *sm_state);
void read_args(sm_state *sm_state);
void end_def(sm_state *sm_state);
void start_apply(sm_state *sm_state);
void add_instruction(sm_state *sm_state);
void begin(sm_state *sm_state)
{
    // puts("begin");
    byte *bp = read_byte(&sm_state->buffer);
    if (bp == NULL)
    {
        // No data, exit.
        sm_state->next = NULL;
        return;
    }
    sm_state->b = *bp;
    byte b = sm_state->b;
    if (is_operation_instr(b))
    {
        if (is_define_limit_instr(b))
        {
            // Define new operation
            sm_state->next = start_define;
            return;
        }
        else
        {
            // Apply operation, repl, undefined
            // puts("Trying to apply def, unimplemented, abort");
            exit(-1);
        }
    }
    else
    {
        // Add litteral, incorrect syntax
        // puts("Lone literal without context, abort");
        exit(-1);
    }
}
void start_define(sm_state *sm_state)
{
    // puts("start_define");
    byte b = sm_state->b;
    byte newOpIdx = b & OPERATION_MASK;
    if (isOpDefined(newOpIdx) != 0)
    {
        // puts("Trying to redefine operation, abort");
        exit(-1);
    }
    init_operation(&sm_state->state.new_op);
    sm_state->state.new_op_Idx = newOpIdx;
    sm_state->next = define_op_next_iter;
}
void define_op_next_iter(sm_state *sm_state)
{
    // puts("define_op_next_iter");
    byte *bp = read_byte(&sm_state->buffer);
    if (bp == NULL)
    {
        // puts("No more data while defining, abort");
        exit(-1);
    }
    sm_state->b = *bp;
    byte b = sm_state->b;
    if (is_operation_instr(b))
    {
        if (is_define_limit_instr(b))
        {
            // End of op def
            sm_state->next = end_def;
            return;
        }
        else // if instr is apply op (new instr to current new op)
        {
            sm_state->next = start_apply;
            return;
        }
    }
    else
    {
        // puts("Lone literal without context, abort");
        exit(-1);
    }
}

void end_def(sm_state *sm_state)
{
    // puts("end_def");
    // End of def, try to create the newly defined op
    int isCorrectlyDefined = add_op(&sm_state->state);
    if (isCorrectlyDefined != 0)
    {
        // op was correctly defined, go back to beginning.
        sm_state->next = begin;
        return;
    }
    else
    {
        // puts("Wrongly defined new op, abort");
        exit(-1);
    }
}

void start_apply(sm_state *sm_state)
{
    // puts("start_apply");
    byte b = sm_state->b;
    int toApplyOpIdx = b & OPERATION_MASK;
    if (isOpDefined(toApplyOpIdx) == 0)
    {
        // puts("Trying to apply missing op, abort");
        exit(-1);
    }
    sm_state->state.applying_op_AppIdx = toApplyOpIdx;
    sm_state->state.applying_op_inCount = CIRCUITS[toApplyOpIdx].n_inputs;
    sm_state->state.applying_op_OutCount = CIRCUITS[toApplyOpIdx].n_outputs;
    sm_state->state.applying_op_literalCount = 0;
    sm_state->next = read_args;
}

void read_args(sm_state *sm_state)
{
    // puts("read_args");
    byte *bp = peek_byte(&sm_state->buffer);
    if (bp == NULL)
    {
        // puts("No more data while defining args, abort");
        exit(-1);
    }
    byte b = *bp;

    if (is_operation_instr(b))
    {
        // puts("We have't finished to defin this instruction, abort");
        exit(-1);
    };
    read_byte(&sm_state->buffer);
    sm_state->b = b;
    // b is lit arg

    // The new operation we are defining.
    Circuit *new_op = &sm_state->state.new_op;

    // Data about the current op application
    int curr_op_nInCount = sm_state->state.applying_op_inCount;
    int curr_op_nOutCount = sm_state->state.applying_op_OutCount;
    int curr_op_expected_args_count = curr_op_nInCount + curr_op_nOutCount;
    int curr_op_processed_args = sm_state->state.applying_op_literalCount;

    // Data for the new operation
    int *in = sm_state->state.in;
    int *med = sm_state->state.med;
    int *out = sm_state->state.out;

    if (curr_op_processed_args < curr_op_nInCount)
    {
        // We are in the input of the current op application.
        // So, the current b should either be an input of the new op or an intermediate
        if (med[b])
        {
            // So, the current b should either be an input of the new op or an intermediate
            // For the new op, we KNOW that b is an intermediate wire.
        }
        else if (out[b])
        {
            // So, the current b should either be an input of the new op or an intermediate
            // Hm, this input was already seen as an output of another application op
            // So it's not an input of the new op, its an intermediate;
            out[b] = 0;
            in[b] = 0;
            med[b] = 1;

            new_op->n_outputs--;
        }
        else
        {
            // So, the current b should either be an input of the new op or an intermediate
            // This input is either a new input of the new op, or an already seen one.
            in[b]++;
            if (in[b] == 1)
            {
                // That's a new input of the new op!
                new_op->n_inputs++;
            }
        }
    }
    else if (curr_op_processed_args < curr_op_expected_args_count)
    {
        // We are in the output of the current op application.
        // So, the current b should either be an output of the new op or an intermediate
        if (med[b])
        {
            // So, the current b should either be an output of the new op or an intermediate
            // For the new op, we KNOW that b is an intermediate wire.
        }
        else if (in[b])
        {
            // So, the current b should either be an output of the new op or an intermediate
            // Hm, this output was already seen as an input of another application op
            // So it's not an output of the new op, its an intermediate;
            out[b] = 0;
            in[b] = 0;
            med[b] = 1;

            // remove the input
            new_op->n_inputs--;
        }
        else
        {
            // So, the current b should either be an output of the new op or an intermediate
            // This output is either a new output of the new op, or an already seen one.
            out[b]++;
            if (out[b] == 1)
            {
                // That's a new output!
                new_op->n_outputs++;
            }
        }
    }
    else
    {
        // puts("Too many arg for apply op, abort");
        exit(-1);
    }

    sm_state->state.applying_op_defining_args[curr_op_processed_args] = b;
    curr_op_processed_args++;

    if (curr_op_processed_args == curr_op_expected_args_count)
    {
        // the current operation was applied
        curr_op_processed_args = 0;
        sm_state->next = add_instruction;
    }
    sm_state->state.applying_op_literalCount = curr_op_processed_args;
    // next is read_args, this method
}

void add_instruction(sm_state *sm_state)
{
    // puts("add_instruction");

    interpreter_state *state = &sm_state->state;

    int expected_args = state->applying_op_inCount + state->applying_op_OutCount;
    int *filled_args = state->applying_op_defining_args;
    build_and_push_instr(&state->new_op, filled_args, expected_args, state->applying_op_AppIdx);

    sm_state->next = define_op_next_iter;
}
