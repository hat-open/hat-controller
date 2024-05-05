#ifndef PY_LUA_INTERPRETER_H
#define PY_LUA_INTERPRETER_H

#include <Python.h>
#include <lua.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyObject ob_base;
    PyObject *luafunction_type;
    lua_State *L;
} Interpreter;


PyObject *create_interpreter_type(PyObject *module);

// [-0, +1, e]
Interpreter *get_interpreter(lua_State *L);

#ifdef __cplusplus
}
#endif

#endif
