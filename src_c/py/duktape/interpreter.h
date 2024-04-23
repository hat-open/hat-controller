#ifndef PY_DUKTAPE_INTERPRETER_H
#define PY_DUKTAPE_INTERPRETER_H

#include <Python.h>
#include <duktape.h>

#include "stash.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyObject ob_base;
    PyObject *jsfunction_type;
    duk_context *ctx;
    stash_id_t next_stash_id;
} Interpreter;


PyObject *create_interpreter_type(PyObject *module);

#ifdef __cplusplus
}
#endif

#endif
