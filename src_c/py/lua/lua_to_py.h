#ifndef PY_LUA_LUA_TO_PY_H
#define PY_LUA_LUA_TO_PY_H

#include <Python.h>
#include <lua.h>

#ifdef __cplusplus
extern "C" {
#endif

// [-1, +1, e]
int lua_to_py(lua_State *L);

#ifdef __cplusplus
}
#endif

#endif
