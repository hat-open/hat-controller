#ifndef PY_LUA_LUA_H
#define PY_LUA_LUA_H

#include <Python.h>
#include <lua.h>

#ifdef __cplusplus
extern "C" {
#endif

// [-n, +0, -]
void clear_lua_stack(lua_State *L);

#ifdef __cplusplus
}
#endif

#endif
