#ifndef PY_LUA_LUAFUNCTION_H
#define PY_LUA_LUAFUNCTION_H

#include <Python.h>
#include <lua.h>

#include "interpreter.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyObject ob_base;
    Interpreter *inter;
    int ref;
} LuaFunction;


PyObject *create_luafunction_type(PyObject *module);

// [-1, +1, e]
int create_luafunction(lua_State *L);

#ifdef __cplusplus
}
#endif

#endif
