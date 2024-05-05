#include "error.h"

#include <lauxlib.h>

#include "pyobject.h"


static int unsafe_py_raise_lua_error(lua_State *L) {
    const char *err = luaL_tolstring(L, -1, NULL);
    PyErr_Format(PyExc_Exception, "lua error: %s",
                 (err ? err : "invalid error"));
    lua_pop(L, 2);
    return 0;
}


// [-1, +(0|1), -]
int py_raise_lua_error(lua_State *L) {
    lua_pushcfunction(L, unsafe_py_raise_lua_error);
    lua_insert(L, -2);

    int err = lua_pcall(L, 1, 0, 0);
    if (err)
        PyErr_SetString(PyExc_Exception, "error raising lua error");

    return err;
}


// [-0, +n, e]
int lua_raise_py_error(lua_State *L, const char *alternative) {
    new_pyobject(L);
    new_pyobject(L);
    new_pyobject(L);

    PyObject *ptype;
    PyObject *pvalue;
    PyObject *ptraceback;
    PyErr_Fetch(&ptype, &pvalue, &ptraceback);

    if (set_pyobject(L, -3, ptype) + set_pyobject(L, -2, pvalue) +
        set_pyobject(L, -1, ptraceback))
        return luaL_error(L, "%s", alternative);

    if (!ptype || !pvalue)
        return luaL_error(L, "%s", alternative);

    new_pyobject(L);
    PyObject *ptype_str = PyObject_GetAttrString(ptype, "__name__");
    if (!ptype_str || set_pyobject(L, -1, ptype_str))
        return luaL_error(L, "%s", alternative);

    new_pyobject(L);
    PyObject *pvalue_str = PyObject_Str(pvalue);
    if (!pvalue_str || set_pyobject(L, -1, pvalue_str))
        return luaL_error(L, "%s", alternative);

    const char *type = PyUnicode_AsUTF8AndSize(ptype_str, NULL);
    const char *value = PyUnicode_AsUTF8AndSize(pvalue_str, NULL);

    if (!type || !value)
        return luaL_error(L, "%s", alternative);

    return luaL_error(L, "%s: %s", type, value);
}
