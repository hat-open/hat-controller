#include "jsfunction.h"

#include "js_to_py.h"
#include "py_to_js.h"


static void free_js_vals(JSContext *ctx, JSValue *vals, size_t vals_len) {
    for (size_t i = 0; i < vals_len; ++i)
        JS_FreeValue(ctx, vals[i]);
}


static PyObject *JsFunction_new(PyTypeObject *type, PyObject *args,
                                PyObject *kwds) {
    JsFunction *self = (JsFunction *)PyType_GenericAlloc(type, 0);
    if (!self)
        return NULL;

    self->inter = NULL;
    self->fn = JS_UNINITIALIZED;

    return (PyObject *)self;
}


static void JsFunction_dealloc(JsFunction *self) {
    if (self->inter) {
        JS_FreeValue(self->inter->ctx, self->fn);
        Py_DECREF(self->inter);
    }

    PyTypeObject *tp = Py_TYPE(self);
    PyObject_Free(self);
    Py_DECREF(tp);
}


static PyObject *JsFunction_call(JsFunction *self, PyObject *args,
                                 PyObject *kwargs) {
    if (!self->inter || JS_IsUninitialized(self->fn)) {
        PyErr_SetString(PyExc_Exception, "function not initialized");
        return NULL;
    }

    Py_ssize_t args_size = PyTuple_Size(args);
    if (args_size < 0) {
        PyErr_SetString(PyExc_Exception, "invalid args length");
        return NULL;
    }

    JSValue vals[args_size];
    for (size_t i = 0; i < args_size; ++i) {
        PyObject *obj = PyTuple_GetItem(args, i);
        if (!obj) {
            free_js_vals(self->inter->ctx, vals, i);
            PyErr_SetString(PyExc_Exception, "invalid args item");
            return NULL;
        }

        vals[i] = py_obj_to_js_val(self->inter->ctx, obj);
        if (JS_IsException(vals[i])) {
            js_val_to_py_obj(self->inter->ctx, vals[i]);
            free_js_vals(self->inter->ctx, vals, i);
            return NULL;
        }
    }

    PyThreadState *state = PyEval_SaveThread();

    JSValue val = JS_Call(self->inter->ctx, self->fn, JS_UNDEFINED, args_size,
                          (JSValueConst *)vals);
    free_js_vals(self->inter->ctx, vals, args_size);

    PyEval_RestoreThread(state);

    PyObject *obj = js_val_to_py_obj(self->inter->ctx, val);
    JS_FreeValue(self->inter->ctx, val);

    return obj;
}


static PyType_Slot jsfunction_type_slots[] = {
    {Py_tp_new, JsFunction_new},
    {Py_tp_dealloc, JsFunction_dealloc},
    {Py_tp_call, JsFunction_call},
    {0, NULL}};


static PyType_Spec jsfunction_type_spec = {
    .name = "hat.controller.interpreters._quickjs.JsFunction",
    .basicsize = sizeof(JsFunction),
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HEAPTYPE,
    .slots = jsfunction_type_slots};


PyObject *create_jsfunction_type(PyObject *module) {
    return PyType_FromModuleAndSpec(module, &jsfunction_type_spec, NULL);
}


JsFunction *create_jsfunction(JSContext *ctx, JSValueConst fn) {
    Interpreter *inter = JS_GetContextOpaque(ctx);
    if (!inter) {
        PyErr_SetString(PyExc_Exception, "interpreter initialization error");
        return NULL;
    }

    JsFunction *obj = (JsFunction *)PyObject_CallNoArgs(inter->jsfunction_type);
    if (!obj)
        return NULL;

    Py_INCREF(inter);
    obj->inter = inter;
    obj->fn = JS_DupValue(ctx, fn);

    return obj;
}
