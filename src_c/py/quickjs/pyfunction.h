#ifndef PY_QUICKJS_PYFUNCTION_H
#define PY_QUICKJS_PYFUNCTION_H

#include <Python.h>
#include <quickjs.h>

#ifdef __cplusplus
extern "C" {
#endif

JSClassID create_pyfunction_class(JSRuntime *rt);
JSValue create_pyfunction(JSContext *ctx, PyObject *fn);

#ifdef __cplusplus
}
#endif

#endif
