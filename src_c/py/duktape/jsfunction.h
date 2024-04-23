#ifndef PY_DUKTAPE_JSFUNCTION_H
#define PY_DUKTAPE_JSFUNCTION_H

#include <Python.h>
#include <duktape.h>

#include "interpreter.h"
#include "safe_call.h"
#include "stash.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyObject ob_base;
    Interpreter *inter;
    stash_id_t fn;
} JsFunction;


PyObject *create_jsfunction_type(PyObject *module);

// ( fn -- ) without data
JsFunction *create_jsfunction(safe_call_ctx_t *cctx);

#ifdef __cplusplus
}
#endif

#endif
