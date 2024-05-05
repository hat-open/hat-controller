#ifndef PY_LUA_PYFUNCTION_H
#define PY_LUA_PYFUNCTION_H

#include <Python.h>
#include <lua.h>

#ifdef __cplusplus
extern "C" {
#endif

// [-0, +1, e]
int create_pyfunction(lua_State *L, PyObject *fn);

#ifdef __cplusplus
}
#endif

#endif
