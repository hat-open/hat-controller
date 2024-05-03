#ifndef PY_QUICKJS_ERROR_H
#define PY_QUICKJS_ERROR_H

#include <Python.h>
#include <quickjs.h>

#ifdef __cplusplus
extern "C" {
#endif

JSValue js_throw_py_err(JSContext *ctx, const char *alternative);
PyObject *py_raise_js_exc(JSContext *ctx);

#ifdef __cplusplus
}
#endif

#endif
