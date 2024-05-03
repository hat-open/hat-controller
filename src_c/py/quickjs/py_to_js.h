#ifndef PY_QUICKJS_PY_TO_JS_H
#define PY_QUICKJS_PY_TO_JS_H

#include <Python.h>
#include <quickjs.h>

#ifdef __cplusplus
extern "C" {
#endif

JSValue py_obj_to_js_val(JSContext *ctx, PyObject *obj);

#ifdef __cplusplus
}
#endif

#endif
