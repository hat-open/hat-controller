#ifndef PY_DUKTAPE_PY_TO_JS_H
#define PY_DUKTAPE_PY_TO_JS_H

#include <Python.h>
#include <duktape.h>

#include "safe_call.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyObject *obj;
} py_to_js_data_t;


// ( ptr -- any ) without data
duk_ret_t py_to_js(safe_call_ctx_t *cctx);

// ( -- any ) with data
duk_ret_t py_to_js_data(safe_call_ctx_t *cctx);

#ifdef __cplusplus
}
#endif

#endif
