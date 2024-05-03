#ifndef PY_QUICKJS_JS_TO_PY_H
#define PY_QUICKJS_JS_TO_PY_H

#include <Python.h>
#include <quickjs.h>

#ifdef __cplusplus
extern "C" {
#endif

PyObject *js_val_to_py_obj(JSContext *ctx, JSValueConst val);

#ifdef __cplusplus
}
#endif

#endif
