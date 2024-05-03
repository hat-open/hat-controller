#include "quickjs.h"


static PyObject *Interpreter_new(PyTypeObject *type, PyObject *args,
                                 PyObject *kwds) {
    Interpreter *self = (Interpreter *)PyType_GenericAlloc(type, 0);
    if (!self)
        return NULL;

    self->jsfunction_type = NULL;
    self->rt = NULL;
    self->ctx = NULL;
    self->pyfunction_cid = JS_INVALID_CLASS_ID;

    ModuleState *state = PyType_GetModuleState(type);
    if (!state) {
        PyErr_SetString(PyExc_Exception, "module initialization error");
        goto error;
    }

    Py_INCREF(state->jsfunction_type);
    self->jsfunction_type = state->jsfunction_type;

    self->rt = JS_NewRuntime();
    if (!self->rt)
        goto error;

    self->ctx = JS_NewContext(self->rt);
    if (!self->ctx)
        goto error;

    self->pyfunction_cid = create_pyfunction_class(self->rt);
    if (self->pyfunction_cid == JS_INVALID_CLASS_ID)
        goto error;

    JS_SetRuntimeOpaque(self->rt, self);
    JS_SetContextOpaque(self->ctx, self);

    return (PyObject *)self;

error:

    if (self->ctx) {
        JS_FreeContext(self->ctx);
        self->ctx = NULL;
    }

    if (self->rt) {
        JS_FreeRuntime(self->rt);
        self->rt = NULL;
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
        JS_FreeContext(self->ctx);

    if (self->rt)
        JS_FreeRuntime(self->rt);

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

    JSValue val = JS_Eval(self->ctx, input, input_len, "", JS_EVAL_TYPE_GLOBAL);

    PyEval_RestoreThread(state);

    PyObject *result = js_val_to_py_obj(self->ctx, val);
    JS_FreeValue(self->ctx, val);

    return result;
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
    .name = "hat.controller.interpreters._quickjs.Interpreter",
    .basicsize = sizeof(Interpreter),
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HEAPTYPE,
    .slots = interpreter_type_slots};


PyObject *create_interpreter_type(PyObject *module) {
    return PyType_FromModuleAndSpec(module, &interpreter_type_spec, NULL);
}
