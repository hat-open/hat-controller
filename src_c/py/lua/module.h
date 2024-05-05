#ifndef PY_LUA_MODULE_H
#define PY_LUA_MODULE_H

#include <Python.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyObject *interpreter_type;
    PyObject *luafunction_type;
} ModuleState;

#ifdef __cplusplus
}
#endif

#endif
