#ifndef PY_QUICKJS_JSFUNCTION_H
#define PY_QUICKJS_JSFUNCTION_H

#include <Python.h>
#include <quickjs.h>

#include "interpreter.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyObject ob_base;
    Interpreter *inter;
    JSValue fn;
} JsFunction;


PyObject *create_jsfunction_type(PyObject *module);
JsFunction *create_jsfunction(JSContext *ctx, JSValueConst fn);

#ifdef __cplusplus
}
#endif

#endif
