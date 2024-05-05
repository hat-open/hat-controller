#ifndef PY_LUA_PY_TO_LUA_H
#define PY_LUA_PY_TO_LUA_H

#include <Python.h>
#include <lua.h>

#ifdef __cplusplus
extern "C" {
#endif

// [-1, +1, e]
int py_to_lua(lua_State *L);

#ifdef __cplusplus
}
#endif

#endif
