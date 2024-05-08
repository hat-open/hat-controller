#ifndef PY_QUICKJS_INTERPRETER_H
#define PY_QUICKJS_INTERPRETER_H

#include <Python.h>
#include <quickjs.h>

#ifndef JS_INVALID_CLASS_ID
#define JS_INVALID_CLASS_ID 0
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyObject ob_base;
    PyObject *jsfunction_type;
    JSRuntime *rt;
    JSContext *ctx;
    JSClassID pyfunction_cid;
} Interpreter;


PyObject *create_interpreter_type(PyObject *module);

#ifdef __cplusplus
}
#endif

#endif
