#include "module.h"

#include "interpreter.h"
#include "jsfunction.h"


static int module_exec(PyObject *module) {
    ModuleState *state = PyModule_GetState(module);
    if (!state)
        return -1;

    state->interpreter_type = NULL;
    state->jsfunction_type = NULL;

    state->interpreter_type = create_interpreter_type(module);
    if (!state->interpreter_type)
        goto error;

    state->jsfunction_type = create_jsfunction_type(module);
    if (!state->jsfunction_type)
        goto error;

    if (PyModule_AddObjectRef(module, "Interpreter", state->interpreter_type))
        goto error;

    if (PyModule_AddObjectRef(module, "JsFunction", state->jsfunction_type))
        goto error;

    return 0;

error:

    if (state->jsfunction_type) {
        Py_DECREF(state->jsfunction_type);
        state->jsfunction_type = NULL;
    }

    if (state->interpreter_type) {
        Py_DECREF(state->interpreter_type);
        state->interpreter_type = NULL;
    }

    return -1;
}


static void module_free(PyObject *module) {
    ModuleState *state = PyModule_GetState(module);
    if (!state)
        return;

    Py_XDECREF(state->interpreter_type);
    Py_XDECREF(state->jsfunction_type);
}


static PyModuleDef_Slot module_slots[] = {{Py_mod_exec, module_exec},
                                          {0, NULL}};


static PyModuleDef module_def = {.m_base = PyModuleDef_HEAD_INIT,
                                 .m_name = "_quickjs",
                                 .m_size = sizeof(ModuleState),
                                 .m_slots = module_slots,
                                 .m_free = (freefunc)module_free};


PyMODINIT_FUNC PyInit__quickjs() { return PyModuleDef_Init(&module_def); }
