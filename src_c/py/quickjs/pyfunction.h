#ifndef PY_QUICKJS_PYFUNCTION_H
#define PY_QUICKJS_PYFUNCTION_H

#include <Python.h>
#include <quickjs.h>

#ifndef JS_INVALID_CLASS_ID
#define JS_INVALID_CLASS_ID 0
#endif

#ifdef __cplusplus
extern "C" {
#endif

JSClassID create_pyfunction_class(JSRuntime *rt);
JSValue create_pyfunction(JSContext *ctx, PyObject *fn);

#ifdef __cplusplus
}
#endif

#endif
