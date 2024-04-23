#ifndef PY_DUKTAPE_JS_TO_PY_H
#define PY_DUKTAPE_JS_TO_PY_H

#include <Python.h>
#include <duktape.h>

#include "safe_call.h"

#ifdef __cplusplus
extern "C" {
#endif

// ( any -- ) without data
PyObject *js_to_py(safe_call_ctx_t *cctx);

#ifdef __cplusplus
}
#endif

#endif
