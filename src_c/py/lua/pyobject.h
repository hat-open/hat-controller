#ifndef PY_LUA_PYOBJECT_H
#define PY_LUA_PYOBJECT_H

#include <Python.h>
#include <lua.h>

#ifdef __cplusplus
extern "C" {
#endif

// [-0, +0, e]
int init_pyobject(lua_State *L);

// [-0, +1, e]
void new_pyobject(lua_State *L);

// [-0, +0, -] - steals obj ref
int set_pyobject(lua_State *L, int index, PyObject *obj);

// [-0, +0, -] - returns borrowed ref
PyObject *get_pyobject(lua_State *L, int index);

#ifdef __cplusplus
}
#endif

#endif
