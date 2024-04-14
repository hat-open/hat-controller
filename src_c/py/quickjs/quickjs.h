#ifndef PY_QUICKJS_H
#define PY_QUICKJS_H

#include <Python.h>
#include <quickjs.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyObject *interpreter_type;
    PyObject *jsfunction_type;
} ModuleState;

typedef struct {
    PyObject ob_base;
    PyObject *jsfunction_type;
    JSRuntime *rt;
    JSContext *ctx;
    JSClassID pyfunction_cid;
} Interpreter;

typedef struct {
    PyObject ob_base;
    Interpreter *inter;
    JSValue fn;
} JsFunction;


PyObject *create_interpreter_type(PyObject *module);
PyObject *create_jsfunction_type(PyObject *module);
JsFunction *create_jsfunction(JSContext *ctx, JSValueConst fn);
JSClassID create_pyfunction_class(JSRuntime *rt);
JSValue create_pyfunction(JSContext *ctx, PyObject *fn);
PyObject *js_val_to_py_obj(JSContext *ctx, JSValueConst val);
JSValue py_obj_to_js_val(JSContext *ctx, PyObject *obj);
JSValue js_throw_py_err(JSContext *ctx, const char *alternative);
PyObject *py_raise_js_exc(JSContext *ctx);

#ifdef __cplusplus
}
#endif

#endif
