#ifndef PY_DUKTAPE_PYFUNCTION_H
#define PY_DUKTAPE_PYFUNCTION_H

#include <Python.h>
#include <duktape.h>

#include "safe_call.h"

#ifdef __cplusplus
extern "C" {
#endif

// ( ptr -- fn ) without data
duk_ret_t create_pyfunction(safe_call_ctx_t *cctx);

#ifdef __cplusplus
}
#endif

#endif
