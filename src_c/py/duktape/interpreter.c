#include "interpreter.h"

#include "js_to_py.h"
#include "module.h"
#include "safe_call.h"
#include "stash.h"


static void fatal_handler(void *udata, const char *msg) {
    fprintf(stderr, "duktape fatal error: %s\n", (msg ? msg : "no message"));
    fflush(stderr);
    abort();
}


static PyObject *Interpreter_new(PyTypeObject *type, PyObject *args,
                                 PyObject *kwds) {
    Interpreter *self = (Interpreter *)PyType_GenericAlloc(type, 0);
    if (!self)
        return NULL;

    self->jsfunction_type = NULL;
    self->ctx = NULL;
    self->next_stash_id = 1;

    ModuleState *state = PyType_GetModuleState(type);
    if (!state) {
        PyErr_SetString(PyExc_Exception, "module initialization error");
        goto error;
    }

    Py_INCREF(state->jsfunction_type);
    self->jsfunction_type = state->jsfunction_type;

    self->ctx = duk_create_heap(NULL, NULL, NULL, NULL, fatal_handler);
    if (!self->ctx)
        goto error;

    stash_put_data_t put_data = {.id = 0, .ptr = self};
    if (safe_call_js(self->ctx, stash_put_data, &put_data, 0)) {
        PyErr_SetString(PyExc_Exception, duk_safe_to_string(self->ctx, -1));
        goto error;
    }
    duk_pop(self->ctx);

    return (PyObject *)self;

error:
    if (self->ctx) {
        duk_destroy_heap(self->ctx);
        self->ctx = NULL;
    }

    if (self->jsfunction_type) {
        Py_DECREF(self->jsfunction_type);
        self->jsfunction_type = NULL;
    }

    Py_DECREF(self);
    return NULL;
}


static void Interpreter_dealloc(Interpreter *self) {
    if (self->ctx)
        duk_destroy_heap(self->ctx);

    if (self->jsfunction_type)
        Py_DECREF(self->jsfunction_type);

    PyTypeObject *tp = Py_TYPE(self);
    PyObject_Free(self);
    Py_DECREF(tp);
}


static PyObject *Interpreter_eval(Interpreter *self, PyObject *args) {
    Py_ssize_t input_len;
    const char *input = PyUnicode_AsUTF8AndSize(args, &input_len);
    if (!input)
        return NULL;

    PyThreadState *state = PyEval_SaveThread();

    duk_int_t err = duk_peval_lstring(self->ctx, input, input_len);

    PyEval_RestoreThread(state);

    if (err) {
        PyErr_SetString(PyExc_Exception, duk_safe_to_string(self->ctx, -1));
        return NULL;
    }

    return safe_call_py(self->ctx, js_to_py, NULL, 1);
}


static PyMethodDef interpreter_methods[] = {
    {.ml_name = "eval",
     .ml_meth = (PyCFunction)Interpreter_eval,
     .ml_flags = METH_O},
    {NULL}};


static PyType_Slot interpreter_type_slots[] = {
    {Py_tp_new, Interpreter_new},
    {Py_tp_dealloc, Interpreter_dealloc},
    {Py_tp_methods, interpreter_methods},
    {0, NULL}};


static PyType_Spec interpreter_type_spec = {
    .name = "hat.controller.interpreters._duktape.Interpreter",
    .basicsize = sizeof(Interpreter),
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HEAPTYPE,
    .slots = interpreter_type_slots};


PyObject *create_interpreter_type(PyObject *module) {
    return PyType_FromModuleAndSpec(module, &interpreter_type_spec, NULL);
}
