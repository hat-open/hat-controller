#ifndef PY_LUA_ERROR_H
#define PY_LUA_ERROR_H

#include <Python.h>
#include <lua.h>

#ifdef __cplusplus
extern "C" {
#endif

// [-1, +(0|1), -]
int py_raise_lua_error(lua_State *L);

// [-0, +n, e]
int lua_raise_py_error(lua_State *L, const char *alternative);

#ifdef __cplusplus
}
#endif

#endif
