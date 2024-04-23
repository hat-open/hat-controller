#include "jsfunction.h"

#include "js_to_py.h"
#include "py_to_js.h"
#include "stash.h"


static PyObject *JsFunction_new(PyTypeObject *type, PyObject *args,
                                PyObject *kwds) {
    JsFunction *self = (JsFunction *)PyType_GenericAlloc(type, 0);
    if (!self)
        return NULL;

    self->inter = NULL;
    self->fn = -1;

    return (PyObject *)self;
}


static void JsFunction_dealloc(JsFunction *self) {
    if (self->inter) {
        Interpreter *inter = self->inter;
        duk_context *ctx = inter->ctx;
        stash_id_t fn = self->fn;

        stash_del_data_t del_data = {.id = self->fn};
        safe_call_js(ctx, stash_del_data, &del_data, 0);
        duk_pop(ctx);

        Py_DECREF(inter);
    }

    PyTypeObject *tp = Py_TYPE(self);
    PyObject_Free(self);
    Py_DECREF(tp);
}


static PyObject *JsFunction_call(JsFunction *self, PyObject *args,
                                 PyObject *kwargs) {
    if (!self->inter) {
        PyErr_SetString(PyExc_Exception, "function not initialized");
        return NULL;
    }

    Py_ssize_t args_size = PyTuple_Size(args);
    if (args_size < 0) {
        PyErr_SetString(PyExc_Exception, "invalid args length");
        return NULL;
    }

    Interpreter *inter = self->inter;
    duk_context *ctx = inter->ctx;
    stash_id_t fn = self->fn;

    stash_get_data_t get_data = {.id = fn};
    if (safe_call_js(ctx, stash_get_data, &get_data, 0)) {
        PyErr_SetString(PyExc_Exception, duk_safe_to_string(ctx, -1));
        duk_pop(ctx);
        return NULL;
    }

    for (size_t i = 0; i < args_size; ++i) {
        PyObject *obj = PyTuple_GetItem(args, i);
        if (!obj) {
            duk_pop_n(ctx, i + 1);
            PyErr_SetString(PyExc_Exception, "invalid args item");
            return NULL;
        }

        py_to_js_data_t data = {.obj = obj};
        if (safe_call_js(ctx, py_to_js_data, &data, 0)) {
            PyErr_SetString(PyExc_Exception, duk_safe_to_string(ctx, -1));
            duk_pop_n(ctx, i + 2);
            return NULL;
        }
    }

    PyThreadState *state = PyEval_SaveThread();

    duk_int_t err = duk_pcall(ctx, args_size);

    PyEval_RestoreThread(state);

    if (err) {
        PyErr_SetString(PyExc_Exception, duk_safe_to_string(ctx, -1));
        duk_pop(ctx);
        return NULL;
    }

    return safe_call_py(ctx, js_to_py, NULL, 1);
}


static PyType_Slot jsfunction_type_slots[] = {
    {Py_tp_new, JsFunction_new},
    {Py_tp_dealloc, JsFunction_dealloc},
    {Py_tp_call, JsFunction_call},
    {0, NULL}};


static PyType_Spec jsfunction_type_spec = {
    .name = "hat.controller.interpreters._duktape.JsFunction",
    .basicsize = sizeof(JsFunction),
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HEAPTYPE,
    .slots = jsfunction_type_slots};


PyObject *create_jsfunction_type(PyObject *module) {
    return PyType_FromModuleAndSpec(module, &jsfunction_type_spec, NULL);
}


// ( fn -- ) without data
JsFunction *create_jsfunction(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    duk_push_int(ctx, 0);
    stash_get(cctx);
    Interpreter *inter = duk_get_pointer(ctx, -1);
    duk_pop(ctx);
    if (!inter) {
        duk_pop(ctx);
        PyErr_SetString(PyExc_Exception, "interpreter initialization error");
        return NULL;
    }

    JsFunction *obj = (JsFunction *)safe_call_add(
        cctx, PyObject_CallNoArgs(inter->jsfunction_type));
    if (!obj) {
        duk_pop(ctx);
        return NULL;
    }

    stash_id_t fn = inter->next_stash_id++;
    duk_push_int(ctx, fn);
    duk_swap_top(ctx, -2);
    stash_put(cctx);

    Py_INCREF(inter);
    obj->inter = inter;
    obj->fn = fn;

    return obj;
}
